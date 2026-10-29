"""Video compression using FFmpeg with GPU and CPU fallback, safe pipes, and responsive cancellation."""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
import subprocess
import threading
import json
import re
import os
import time

from .task import CompressionTask, TaskStatus
from .hardware import HardwareInfo, list_ffmpeg_encoders
from utils.process import hidden_subprocess_kwargs

ProgressCB = Callable[[float], None]


def _get_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, timeout=30,
            **hidden_subprocess_kwargs()
        )
        data = json.loads(r.stdout)
        dur = float(data.get("format", {}).get("duration", 0))
        if dur:
            return dur
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                dur = float(s.get("duration", 0))
                if dur:
                    return dur
    except Exception:
        pass
    return 0.0


def _get_video_codec(path: Path) -> str:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "json", str(path)],
            capture_output=True, text=True, timeout=15,
            **hidden_subprocess_kwargs()
        )
        d = json.loads(r.stdout)
        return d["streams"][0]["codec_name"] if d.get("streams") else "unknown"
    except Exception:
        return "unknown"


def _build_cmd(src: Path, dst: Path, hw: HardwareInfo, settings: dict) -> tuple[list[str], str]:
    codec = settings.get("codec", "h265")
    quality = int(settings.get("video_quality", settings.get("quality", 28)))
    resolution = settings.get("resolution", "original")
    fps = settings.get("fps", "original")
    use_hw = settings.get("use_hw", True)

    vf_filters = []
    if resolution != "original":
        w, h = {
            "4k": (3840, 2160), "1080p": (1920, 1080),
            "720p": (1280, 720), "480p": (854, 480),
        }.get(resolution, (0, 0))
        if w:
            vf_filters.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease")

    if fps != "original":
        vf_filters.append(f"fps={fps}")

    audio_args = ["-c:a", "aac", "-b:a", "128k"]

    if use_hw and hw.has_nvenc and codec in ("h265", "h264"):
        enc = "hevc_nvenc" if codec == "h265" else "h264_nvenc"
        vf = ",".join(vf_filters) if vf_filters else None
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if vf:
            cmd += ["-vf", vf]
        cmd += ["-c:v", enc, "-cq", str(quality), "-preset", "p4"]
        cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                             "-progress", "pipe:1", str(dst)]
        return cmd, f"NVENC ({enc})"

    if use_hw and getattr(hw, "has_amf", False) and codec in ("h265", "h264"):
        enc = "hevc_amf" if codec == "h265" else "h264_amf"
        vf = ",".join(vf_filters) if vf_filters else None
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if vf:
            cmd += ["-vf", vf]
        cmd += ["-c:v", enc, "-quality", "speed", "-rc", "cqp",
                "-qp_i", str(quality), "-qp_p", str(quality)]
        cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                             "-progress", "pipe:1", str(dst)]
        return cmd, f"AMF ({enc})"

    if use_hw and hw.has_vaapi and codec in ("h265", "h264"):
        enc = "hevc_vaapi" if codec == "h265" else "h264_vaapi"
        hw_vf = ["format=nv12", "hwupload"]
        all_vf = vf_filters + hw_vf
        vf_str = ",".join(all_vf)
        async_depth = int(settings.get("gpu_async_depth", 4))
        cmd = ["ffmpeg", "-y", "-vaapi_device", hw.vaapi_device,
               "-i", str(src), "-vf", vf_str,
               "-c:v", enc, "-async_depth", str(async_depth), "-qp", str(quality)]
        cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                             "-progress", "pipe:1", str(dst)]
        return cmd, f"VAAPI ({enc})"

    if use_hw and hw.has_qsv and codec in ("h265", "h264"):
        enc = "hevc_qsv" if codec == "h265" else "h264_qsv"
        vf = ",".join(vf_filters) if vf_filters else None
        cmd = ["ffmpeg", "-y", "-i", str(src)]
        if vf:
            cmd += ["-vf", vf]
        cmd += ["-c:v", enc, "-global_quality", str(quality)]
        cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                             "-progress", "pipe:1", str(dst)]
        return cmd, f"QSV ({enc})"

    enc_map = {"h265": "libx265", "h264": "libx264", "av1": "libaom-av1"}
    enc = enc_map.get(codec, "libx265")

    # Smart fallback based on available FFmpeg encoders
    available = set(list_ffmpeg_encoders())
    fallback_note = ""
    if codec == "h265" and "libx265" not in available:
        if "libsvtav1" in available:
            enc = "libsvtav1"
            fallback_note = " (h265 fallback -> SVT-AV1)"
        elif "libopenh264" in available:
            enc = "libopenh264"
            fallback_note = " (h265 fallback -> OpenH264)"
    elif codec == "av1":
        if "libsvtav1" in available:
            enc = "libsvtav1"
    elif codec == "h264":
        if "libx264" not in available and "libopenh264" in available:
            enc = "libopenh264"
            fallback_note = " (h264 fallback -> OpenH264)"

    vf = ",".join(vf_filters) if vf_filters else None
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if vf:
        cmd += ["-vf", vf]

    # CPU thread allocation: 0 lets FFmpeg automatically allocate all available CPU cores
    cpu_threads = int(settings.get("cpu_threads", 0))
    threads_arg = ["-threads", str(cpu_threads)]

    if enc == "libsvtav1":
        cmd += ["-c:v", enc, "-crf", str(quality), "-preset", "8"] + threads_arg
    elif enc == "libopenh264":
        cmd += ["-c:v", enc, "-b:v", "2M"] + threads_arg
    elif codec == "av1":
        cmd += ["-c:v", enc, "-crf", str(quality), "-cpu-used", "4"] + threads_arg
    else:
        cmd += ["-c:v", enc, "-crf", str(quality), "-preset", "fast"] + threads_arg

    cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                         "-progress", "pipe:1", str(dst)]
    return cmd, f"CPU ({enc}{fallback_note})"


def _run_ffmpeg(cmd: list, duration: float, progress_cb: ProgressCB,
                cancel_event: threading.Event, base_pct: float = 5.0) -> tuple[int, str]:
    """
    Run an ffmpeg command without pipe buffer deadlocks.
    Reads progress from stdout and error output from stderr concurrently.
    Periodically checks cancel_event to guarantee prompt cancellation.
    """
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        **hidden_subprocess_kwargs()
    )

    from collections import deque
    stderr_chunks: deque[str] = deque(maxlen=100)

    def _drain_stderr():
        try:
            if proc.stderr:
                for line in iter(proc.stderr.readline, ""):
                    if line:
                        stderr_chunks.append(line)
        except Exception:
            pass

    stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
    stderr_thread.start()

    time_re = re.compile(r"out_time_ms=(\d+)")

    def _drain_stdout():
        try:
            if proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    if not line:
                        break
                    m = time_re.search(line)
                    if m and duration > 0:
                        current_s = int(m.group(1)) / 1_000_000
                        pct = min(98.0, base_pct + (current_s / duration) * (98.0 - base_pct))
                        progress_cb(pct)
        except Exception:
            pass

    stdout_thread = threading.Thread(target=_drain_stdout, daemon=True)
    stdout_thread.start()

    try:
        while proc.poll() is None:
            if cancel_event.is_set():
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                break
            time.sleep(0.08)

        proc.wait()
    finally:
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        try:
            if proc.stderr:
                proc.stderr.close()
        except Exception:
            pass

    stdout_thread.join(timeout=1.0)
    stderr_thread.join(timeout=1.0)

    err_msg = "".join(stderr_chunks).strip()
    return proc.returncode, err_msg


def compress_video(task: CompressionTask, settings: dict,
                   hw: HardwareInfo, progress_cb: ProgressCB,
                   cancel_event: Optional[threading.Event] = None) -> None:
    _cancel = cancel_event or threading.Event()

    def _cancelled() -> bool:
        return _cancel.is_set()

    src = task.path
    dst = task.output_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = dst.parent / f".tmp_mc_{task.id}_{src.stem}.mp4"

    try:
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        progress_cb(2.0)

        if task.orig_size == 0 and src.exists():
            task.orig_size = src.stat().st_size

        if _cancelled():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        if settings.get("skip_hevc", True):
            codec = _get_video_codec(src)
            if codec in ("hevc", "h265", "av1"):
                task.status = TaskStatus.SKIPPED
                task.new_size = task.orig_size
                task.encoder_used = f"Skipped (already {codec})"
                progress_cb(100.0)
                return

        if _cancelled():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        duration = _get_duration(src)
        progress_cb(5.0)

        cmd, label = _build_cmd(src, tmp_path, hw, settings)
        rc, err_out = _run_ffmpeg(cmd, duration, progress_cb, _cancel, base_pct=5.0)

        if _cancelled():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        # Fallback to CPU encode if hardware acceleration failed
        if rc != 0 and settings.get("use_hw", True):
            tmp_path.unlink(missing_ok=True)
            if _cancelled():
                task.status = TaskStatus.CANCELLED
                progress_cb(100.0)
                return

            cpu_settings = {**settings, "use_hw": False}
            cmd_cpu, label = _build_cmd(src, tmp_path, hw, cpu_settings)
            label = "CPU (GPU fallback)"
            rc, err_out = _run_ffmpeg(cmd_cpu, duration, progress_cb, _cancel, base_pct=5.0)

            if _cancelled():
                task.status = TaskStatus.CANCELLED
                progress_cb(100.0)
                return

        if rc != 0 or not tmp_path.exists():
            if "Unknown encoder" in err_out:
                codec_name = settings.get("codec", "video")
                raise RuntimeError(
                    f"FFmpeg lacks '{codec_name}' encoder. On Fedora Linux, install full FFmpeg from RPM Fusion: "
                    "'sudo dnf swap ffmpeg-free ffmpeg --allowerasing' or select AV1 in Settings."
                )

            err_lines = [l.strip() for l in err_out.splitlines() if l.strip()]
            meaningful = [
                l for l in err_lines
                if any(k in l.lower() for k in ("error", "invalid", "failed", "cannot", "unknown", "denied", "no such", "not found", "abort"))
            ]
            if not meaningful:
                meaningful = err_lines[-6:] if err_lines else [f"FFmpeg exited with code {rc}"]
            detail = "\n".join(meaningful[-6:])
            raise RuntimeError(f"FFmpeg encoding failed (exit code {rc}):\n{detail}")

        new_size = tmp_path.stat().st_size
        should_replace = (new_size < task.orig_size) or (task.orig_size == 0)
        if should_replace:
            if dst != src and src.exists() and task.output_dir is None:
                src.unlink()
            import shutil
            shutil.move(str(tmp_path), str(dst))
        else:
            tmp_path.unlink(missing_ok=True)
            new_size = task.orig_size

        task.new_size = new_size
        task.encoder_used = label
        task.status = TaskStatus.DONE
        progress_cb(100.0)

    except Exception as e:
        task.status = TaskStatus.ERROR
        task.error_msg = str(e)
        progress_cb(100.0)
    finally:
        tmp_path.unlink(missing_ok=True)
        task.end_time = time.time()
