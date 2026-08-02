"""Hardware detection — GPU encoders, CPU info, live utilization."""
from __future__ import annotations
import os
import subprocess
import tempfile
import time
import platform
from dataclasses import dataclass, field
from typing import Optional

from utils.process import hidden_subprocess_kwargs


# ── Data class ───────────────────────────────────────────────────────────────

@dataclass
class HardwareInfo:
    has_vaapi:    bool = False
    vaapi_device: str  = "/dev/dri/renderD128"
    has_nvenc:    bool = False
    has_amf:      bool = False  # AMD Advanced Media Framework (Windows)
    has_qsv:      bool = False
    has_d3d11va:  bool = False  # Windows DirectX GPU acceleration
    cpu_threads:  int  = 4
    cpu_name:     str  = "Unknown CPU"
    gpu_name:     str  = "Unknown GPU"
    platform:     str  = "unknown"  # linux, windows, darwin

    # Diagnostics collected during detection
    diag_log:     list[str] = field(default_factory=list)

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def has_any_gpu(self) -> bool:
        return self.has_nvenc or self.has_amf or self.has_vaapi or self.has_qsv

    @property
    def best_video_encoder(self) -> str:
        if self.has_nvenc:  return "nvenc"
        if self.has_amf:    return "amf"
        if self.has_vaapi:  return "vaapi"
        if self.has_qsv:    return "qsv"
        return "cpu"

    @property
    def hw_summary(self) -> str:
        parts = []
        if self.has_nvenc:  parts.append("NVIDIA NVENC")
        if self.has_amf:    parts.append("AMD AMF")
        if self.has_d3d11va: parts.append("DirectX (D3D11VA)")
        if self.has_vaapi:  parts.append(f"VAAPI ({os.path.basename(self.vaapi_device)})")
        if self.has_qsv:    parts.append("Intel QSV")
        if not parts:       return "CPU only"
        return " + ".join(parts)

    @property
    def encoder_list(self) -> list[str]:
        enc = []
        if self.has_nvenc:  enc += ["hevc_nvenc", "h264_nvenc"]
        if self.has_amf:    enc += ["hevc_amf", "h264_amf"]
        if self.has_vaapi:  enc += ["hevc_vaapi", "h264_vaapi"]
        if self.has_qsv:    enc += ["hevc_qsv", "h264_qsv"]
        enc += ["libx265", "libx264"]
        return enc


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, env={**os.environ, "LANG": "C"},
            **hidden_subprocess_kwargs()
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def _cleanup(*paths: str):
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass


def _test_encode(cmd: list[str], out_path: str) -> tuple[bool, str]:
    """Run a test encode, return (success, stderr)."""
    rc, _, stderr = _run(cmd, timeout=20)
    _cleanup(out_path)
    return rc == 0, stderr


def _probe_encoder(info: HardwareInfo, label: str, encoders: list[str],
                   extra_args: list[str] | None = None) -> tuple[bool, str | None]:
    """Try one or more FFmpeg encoders and return the first working encoder."""
    errors = []
    for encoder in encoders:
        tmp = os.path.join(tempfile.gettempdir(), f"_mc_{label.lower()}_{os.getpid()}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x144:rate=5",
            "-c:v", encoder,
        ]
        if extra_args:
            cmd += extra_args
        cmd += ["-loglevel", "error", tmp]
        ok, stderr = _test_encode(cmd, tmp)
        if ok:
            info.diag_log.append(f"{label}: OK ({encoder})")
            return True, encoder
        errors.append(f"{encoder}: {stderr.strip()[:100]}")
    info.diag_log.append(f"{label}: FAIL - {' | '.join(errors)[:180]}")
    return False, None


# ── Encoder probes ────────────────────────────────────────────────────────────

def _probe_vaapi(info: HardwareInfo) -> bool:
    if info.platform != "linux":
        return False
    devices = []
    dri_dir = "/dev/dri"
    if os.path.isdir(dri_dir):
        for name in sorted(os.listdir(dri_dir)):
            if name.startswith("renderD"):
                devices.append(os.path.join(dri_dir, name))

    if not devices:
        info.diag_log.append("VAAPI: no /dev/dri/renderD* devices found")
        return False

    for dev in devices:
        tmp = os.path.join(tempfile.gettempdir(), f"_mc_vaapi_{os.getpid()}.mp4")
        ok, stderr = _test_encode([
            "ffmpeg", "-y",
            "-vaapi_device", dev,
            "-f", "lavfi", "-i", "testsrc=duration=0.1:size=256x144:rate=5",
            "-vf", "format=nv12,hwupload",
            "-c:v", "hevc_vaapi", "-qp", "30",
            "-loglevel", "error",
            tmp,
        ], tmp)
        if ok:
            info.diag_log.append(f"VAAPI: OK on {dev}")
            info.has_vaapi   = True
            info.vaapi_device = dev
            return True
        else:
            info.diag_log.append(
                f"VAAPI: FAIL on {dev} — {stderr.strip()[:120]}"
            )
    return False


def _probe_nvenc(info: HardwareInfo) -> bool:
    ok, _ = _probe_encoder(info, "NVENC", ["hevc_nvenc", "h264_nvenc"], ["-preset", "p1"])
    if ok:
        info.has_nvenc = True
        return True
    return False


def _probe_amf(info: HardwareInfo) -> bool:
    """Probe AMD AMF hardware encoding on Windows."""
    if info.platform != "windows":
        return False
    ok, _ = _probe_encoder(info, "AMF", ["hevc_amf", "h264_amf"], ["-quality", "speed"])
    if ok:
        info.has_amf = True
        return True
    return False


def _probe_qsv(info: HardwareInfo) -> bool:
    ok, _ = _probe_encoder(info, "QSV", ["hevc_qsv", "h264_qsv"])
    if ok:
        info.has_qsv = True
        return True
    return False


def _probe_d3d11va(info: HardwareInfo) -> bool:
    """Detect DirectX 11 decode acceleration for diagnostics."""
    if info.platform != "windows":
        return False
    rc, out, _ = _run(["ffmpeg", "-hide_banner", "-hwaccels"], timeout=10)
    if rc == 0 and "d3d11va" in out.lower():
        info.diag_log.append("D3D11VA: OK (decode)")
        info.has_d3d11va = True
        return True
    info.diag_log.append("D3D11VA: not listed by FFmpeg")
    return False


def _detect_gpu_name(info: HardwareInfo):
    """Try platform-specific GPU detection."""
    if info.platform == "windows":
        _detect_gpu_name_windows(info)
    elif info.platform == "linux":
        _detect_gpu_name_linux(info)
    # macOS/darwin could be added here


def _detect_gpu_name_linux(info: HardwareInfo):
    """Linux GPU detection via lspci and /sys."""
    rc, out, _ = _run(["lspci", "-mm"])
    if rc == 0:
        for line in out.splitlines():
            ll = line.lower()
            if any(k in ll for k in ("vga", "3d controller", "display")):
                # lspci -mm: "00:00.0" "Class" "Vendor" "Device" ...
                parts = [p.strip('"') for p in line.split('"')]
                name = " ".join(p for p in parts[3:6] if p and "[" not in p)
                if name.strip():
                    info.gpu_name = name.strip()
                    return

    # Fallback: lspci plain
    rc, out, _ = _run(["lspci"])
    if rc == 0:
        for line in out.splitlines():
            ll = line.lower()
            if any(k in ll for k in ("vga", "3d", "display")):
                info.gpu_name = line.split(":", 2)[-1].strip()
                return

    # Fallback: /sys/class/drm
    for path in [
        "/sys/class/drm/card0/device/product_name",
        "/sys/class/drm/card1/device/product_name",
    ]:
        try:
            info.gpu_name = open(path).read().strip()
            return
        except OSError:
            pass


def _detect_gpu_name_windows(info: HardwareInfo):
    """Windows GPU detection via WMIC."""
    rc, out, _ = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_VideoController | "
        "Where-Object { $_.Name } | "
        "ForEach-Object { $_.Name }"
    ], timeout=10)
    if rc == 0 and out.strip():
        names = [line.strip() for line in out.splitlines() if line.strip()]
        if names:
            info.gpu_name = " + ".join(names)
            return

    # Try WMIC first
    rc, out, _ = _run(["wmic", "path", "win32_VideoController", "get", "name"], timeout=10)
    if rc == 0:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if len(lines) > 1:  # Skip header
            info.gpu_name = lines[1]
            return
    
    # Fallback: try PowerShell
    rc, out, _ = _run([
        "powershell", "-Command",
        "Get-WmiObject Win32_VideoController | Select-Object -ExpandProperty Name"
    ], timeout=10)
    if rc == 0 and out.strip():
        info.gpu_name = out.strip()
        return


def _detect_cpu_name(info: HardwareInfo):
    """Try platform-specific CPU detection."""
    if info.platform == "windows":
        _detect_cpu_name_windows(info)
    elif info.platform == "linux":
        _detect_cpu_name_linux(info)
    # macOS/darwin could be added here


def _detect_cpu_name_linux(info: HardwareInfo):
    """Linux CPU detection via /proc/cpuinfo."""
    try:
        for line in open("/proc/cpuinfo"):
            if line.startswith("model name"):
                info.cpu_name = line.split(":", 1)[1].strip()
                return
    except OSError:
        pass


def _detect_cpu_name_windows(info: HardwareInfo):
    """Windows CPU detection via WMIC."""
    rc, out, _ = _run([
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name"
    ], timeout=10)
    if rc == 0 and out.strip():
        info.cpu_name = out.strip()
        return

    rc, out, _ = _run(["wmic", "cpu", "get", "name"], timeout=10)
    if rc == 0:
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        if len(lines) > 1:  # Skip header
            info.cpu_name = lines[1]
            return


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _get_cache_path() -> str:
    """Get cross-platform cache path."""
    if platform.system() == "Windows":
        return os.path.expandvars(r"%APPDATA%\MediaCrush\hw_cache.json")
    else:
        return os.path.expanduser("~/.config/mediacrush/hw_cache.json")

_CACHE_PATH = _get_cache_path()
_CACHE_TTL  = 86400   # re-probe after 24 hours


def _load_cache() -> HardwareInfo | None:
    import json, time
    try:
        with open(_CACHE_PATH) as f:
            d = json.load(f)
        if time.time() - d.get("_ts", 0) > _CACHE_TTL:
            return None
        info = HardwareInfo(
            has_vaapi    = d.get("has_vaapi", False),
            vaapi_device = d.get("vaapi_device", "/dev/dri/renderD128"),
            has_nvenc    = d.get("has_nvenc", False),
            has_amf      = d.get("has_amf", False),
            has_qsv      = d.get("has_qsv", False),
            has_d3d11va  = d.get("has_d3d11va", False),
            cpu_threads  = d.get("cpu_threads", os.cpu_count() or 4),
            cpu_name     = d.get("cpu_name", "Unknown CPU"),
            gpu_name     = d.get("gpu_name", "Unknown GPU"),
            platform     = d.get("platform", platform.system().lower()),
        )
        info.diag_log.append("[cache] Loaded from disk — skipping probe tests")
        return info
    except Exception:
        return None


def _save_cache(info: HardwareInfo):
    import json, time
    os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
    try:
        with open(_CACHE_PATH, "w") as f:
            json.dump({
                "_ts":         time.time(),
                "has_vaapi":   info.has_vaapi,
                "vaapi_device":info.vaapi_device,
                "has_nvenc":   info.has_nvenc,
                "has_amf":     info.has_amf,
                "has_qsv":     info.has_qsv,
                "has_d3d11va":  info.has_d3d11va,
                "cpu_threads": info.cpu_threads,
                "cpu_name":    info.cpu_name,
                "gpu_name":    info.gpu_name,
                "platform":    info.platform,
            }, f)
    except Exception:
        pass


# ── Main detection function ───────────────────────────────────────────────────

def detect_hardware(force: bool = False) -> HardwareInfo:
    if not force:
        cached = _load_cache()
        if cached is not None:
            return cached

    info = HardwareInfo()
    info.platform = platform.system().lower()
    info.cpu_threads = os.cpu_count() or 4

    _detect_cpu_name(info)
    _detect_gpu_name(info)

    info.diag_log.append(f"Platform: {info.platform}")
    info.diag_log.append(f"CPU: {info.cpu_name} ({info.cpu_threads} threads)")
    info.diag_log.append(f"GPU name: {info.gpu_name}")

    # Probe GPU encoders based on platform
    _probe_nvenc(info)  # Works on both Linux and Windows
    if info.platform == "linux":
        _probe_vaapi(info)
        _probe_qsv(info)
    elif info.platform == "windows":
        _probe_amf(info)
        _probe_qsv(info)
        _probe_d3d11va(info)

    info.diag_log.append(
        f"Result: {info.hw_summary} | best_encoder={info.best_video_encoder}"
    )
    _save_cache(info)
    return info


# ── Live utilization helpers (optional, non-fatal) ────────────────────────────

def get_cpu_usage() -> float:
    """Return CPU usage 0-100."""
    try:
        import psutil
        return psutil.cpu_percent(interval=None)
    except ImportError:
        return 0.0


def get_ram_usage() -> tuple[float, float]:
    """Return (used_gb, total_gb)."""
    try:
        import psutil
        m = psutil.virtual_memory()
        return m.used / 1e9, m.total / 1e9
    except ImportError:
        return 0.0, 0.0


def get_gpu_usage() -> tuple[float, float, str]:
    """Return (util_pct, vram_used_gb, label). Non-fatal if unavailable."""
    # Try NVIDIA
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        util  = pynvml.nvmlDeviceGetUtilizationRates(h).gpu
        mem   = pynvml.nvmlDeviceGetMemoryInfo(h)
        vram  = mem.used / 1e9
        name  = pynvml.nvmlDeviceGetName(h)
        return float(util), vram, name
    except Exception:
        pass

    # Try VAAPI via intel_gpu_top / radeontop (just mark as available)
    try:
        rc, out, _ = _run(["vainfo", "--display", "drm", "--device", "/dev/dri/renderD128"],
                          timeout=3)
        if rc == 0 and "hevc" in out.lower():
            return -1.0, 0.0, "VAAPI (AMD/Intel)"  # -1 = available but no util metric
    except Exception:
        pass

    return 0.0, 0.0, "N/A"


def get_ffmpeg_version() -> str:
    rc, out, _ = _run(["ffmpeg", "-version"], timeout=5)
    if rc == 0:
        first = out.splitlines()[0] if out else ""
        return first.replace("ffmpeg version", "").strip().split(" ")[0]
    return "not found"


def list_ffmpeg_encoders() -> list[str]:
    rc, out, _ = _run(["ffmpeg", "-encoders", "-v", "quiet"], timeout=10)
    if rc != 0:
        return []
    enc = []
    for line in out.splitlines():
        stripped = line.strip()
        if stripped and stripped[0] in ("V", "A", "S"):
            parts = stripped.split()
            if parts:
                enc.append(parts[1] if len(parts) > 1 else parts[0])
    return enc
