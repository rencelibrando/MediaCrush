"""Video compression using FFmpeg with GPU + CPU fallback."""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
import subprocess
import threading
import json
import re
import os
import time
import tempfile

from .task import CompressionTask, TaskStatus
from .hardware import HardwareInfo

ProgressCB = Callable[[float], None]


def _get_duration(path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, timeout=30
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
            capture_output=True, text=True, timeout=15
        )
        d = json.loads(r.stdout)
        return d["streams"][0]["codec_name"] if d.get("streams") else "unknown"
    except Exception:
        return "unknown"


def _build_cmd(src: Path, dst: Path, hw: HardwareInfo, settings: dict) -> tuple[list[str], str]:
    """Build ffmpeg command. Returns (cmd, encoder_label)."""
    codec       = settings.get("codec", "h265")
    quality     = int(settings.get("video_quality", settings.get("quality", 28)))
    resolution  = settings.get("resolution", "original")
    fps         = settings.get("fps", "original")
    use_hw      = settings.get("use_hw", True)

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

    # --- GPU path ---
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

    if use_hw and hw.has_vaapi and codec in ("h265", "h264"):
        enc     = "hevc_vaapi" if codec == "h265" else "h264_vaapi"
        hw_vf   = ["format=nv12", "hwupload"]
        all_vf  = vf_filters + hw_vf
        vf_str  = ",".join(all_vf)
        cmd = ["ffmpeg", "-y", "-vaapi_device", hw.vaapi_device,
               "-i", str(src), "-vf", vf_str,
               "-c:v", enc, "-qp", str(quality)]
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

    # --- CPU path ---
    enc_map = {"h265": "libx265", "h264": "libx264", "av1": "libaom-av1"}
    enc = enc_map.get(codec, "libx265")
    vf = ",".join(vf_filters) if vf_filters else None
    cmd = ["ffmpeg", "-y", "-i", str(src)]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", enc, "-crf", str(quality), "-preset", "fast",
            "-threads", "1"]
    if codec == "av1":
        cmd = [c for c in cmd if c not in ("-preset", "fast", "-threads", "1")]
        cmd += ["-cpu-used", "4"]
    cmd += audio_args + ["-movflags", "+faststart", "-loglevel", "error",
                         "-progress", "pipe:1", str(dst)]
    return cmd, f"CPU ({enc})"


def _run_ffmpeg(cmd: list, duration: float, progress_cb: ProgressCB,
                cancel_event: threading.Event, base_pct: float = 5.0) -> subprocess.Popen:
    """
    Run an ffmpeg command, updating progress and terminating immediately
    if cancel_event fires. Returns the finished Popen object.
    """
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )
    time_re = re.compile(r"out_time_ms=(\d+)")
    while proc.poll() is None:
        if cancel_event.is_set():
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            return proc
        line = proc.stdout.readline()
        if not line:
            continue
        m = time_re.search(line)
        if m and duration > 0:
            current_s = int(m.group(1)) / 1_000_000
            pct = min(98.0, base_pct + (current_s / duration) * (98.0 - base_pct))
            progress_cb(pct)
    proc.wait()
    return proc


def compress_video(task: CompressionTask, settings: dict,
                   hw: HardwareInfo, progress_cb: ProgressCB,
                   cancel_event: Optional[threading.Event] = None) -> None:
    _cancel = cancel_event or threading.Event()  # no-op event if not provided

    def _cancelled() -> bool:
        return _cancel.is_set()

    try:
        task.status     = TaskStatus.RUNNING
        task.start_time = time.time()
        progress_cb(2.0)

        src = task.path
        dst = task.output_path
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Re-read orig_size if it wasn't captured at task creation
        if task.orig_size == 0 and src.exists():
            task.orig_size = src.stat().st_size

        if _cancelled():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        # Skip if already HEVC and user wants to skip
        if settings.get("skip_hevc", True):
            codec = _get_video_codec(src)
            if codec in ("hevc", "h265", "av1"):
                task.status       = TaskStatus.SKIPPED
                task.new_size     = task.orig_size
                task.encoder_used = f"Skipped (already {codec})"
                progress_cb(100.0)
                return

        if _cancelled():
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        duration = _get_duration(src)
        progress_cb(5.0)

        tmp_path = src.with_suffix(".tmp_mc.mp4")
        cmd, label = _build_cmd(src, tmp_path, hw, settings)

        proc = _run_ffmpeg(cmd, duration, progress_cb, _cancel, base_pct=5.0)

        if _cancelled():
            tmp_path.unlink(missing_ok=True)
            task.status = TaskStatus.CANCELLED
            progress_cb(100.0)
            return

        # GPU encode failed → retry with CPU
        if proc.returncode != 0 and settings.get("use_hw", True):
            tmp_path.unlink(missing_ok=True)
            if _cancelled():
                task.status = TaskStatus.CANCELLED
                progress_cb(100.0)
                return
            cpu_settings = {**settings, "use_hw": False}
            cmd_cpu, label = _build_cmd(src, tmp_path, hw, cpu_settings)
            label = "CPU↩ (GPU failed)"
            proc = _run_ffmpeg(cmd_cpu, duration, progress_cb, _cancel, base_pct=5.0)

            if _cancelled():
                tmp_path.unlink(missing_ok=True)
                task.status = TaskStatus.CANCELLED
                progress_cb(100.0)
                return

        if proc.returncode != 0 or not tmp_path.exists():
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"ffmpeg failed: {stderr[:200]}")

        new_size = tmp_path.stat().st_size
        should_replace = (new_size < task.orig_size) or (task.orig_size == 0)
        if should_replace:
            if dst != src and src.exists() and task.output_dir is None:
                src.unlink()
            import shutil
            shutil.move(str(tmp_path), str(dst))
        else:
            tmp_path.unlink(missing_ok=True)
            new_size = task.orig_size  # no benefit

        task.new_size     = new_size
        task.encoder_used = label
        task.status       = TaskStatus.DONE
        progress_cb(100.0)

    except Exception as e:
        task.status    = TaskStatus.ERROR
        task.error_msg = str(e)
        try:
            src.with_suffix(".tmp_mc.mp4").unlink(missing_ok=True)
        except Exception:
            pass
        progress_cb(100.0)
    finally:
        task.end_time = time.time()
