"""Persistent settings stored in ~/.config/mediacrush/settings.json."""
from __future__ import annotations
import json
import os
import platform
from pathlib import Path
from typing import Any

# Cross-platform config path
if platform.system() == "Windows":
    CONFIG_PATH = Path(os.path.expandvars(r"%APPDATA%\MediaCrush\settings.json"))
else:
    CONFIG_PATH = Path.home() / ".config" / "mediacrush" / "settings.json"

def _get_default_workers() -> dict:
    """Auto-detect optimal worker counts based on hardware."""
    cpu_count = os.cpu_count() or 4
    # For GPU: use 1-2 workers typically (GPU encoders are parallel internally)
    # For CPU: use all available threads for maximum performance
    return {
        "gpu_workers": min(2, cpu_count // 2),  # Conservative GPU workers
        "cpu_workers": cpu_count,  # Max CPU workers
    }

DEFAULTS: dict = {
    "image": {
        "preset":         "balanced",
        "quality":        85,
        "strip_metadata": False,
        "resize_max_px":  None,
    },
    "video": {
        "codec":     "h265",
        "quality":   28,
        "resolution": "original",
        "fps":        "original",
        "skip_hevc":  True,
    },
    "engine": {
        **_get_default_workers(),
        "output_mode": "inplace",   # inplace | alongside | custom
        "output_dir":  "",
    },
    "ui": {
        "theme":    "dark",
        "last_dir": "",
        "window_geometry": None,
    },
}


class Settings:
    def __init__(self):
        self._data: dict = {}
        self.load()

    def load(self):
        self._data = _deep_copy(DEFAULTS)
        if CONFIG_PATH.exists():
            try:
                saved = json.loads(CONFIG_PATH.read_text())
                _deep_merge(self._data, saved)
            except Exception:
                pass

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self._data, indent=2))

    # Dot-path access: get("video.codec"), set("ui.theme", "light")
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        node = self._data
        for p in parts:
            if not isinstance(node, dict) or p not in node:
                return default
            node = node[p]
        return node

    def set(self, key: str, value: Any):
        parts = key.split(".")
        node = self._data
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = value

    def section(self, name: str) -> dict:
        return dict(self._data.get(name, {}))

    def set_section(self, name: str, data: dict):
        self._data[name] = data

    def compression_settings(self) -> dict:
        """Merged dict passed to the engine — keeps image/video quality separate."""
        img = self.section("image")
        vid = self.section("video")
        eng = self.section("engine")
        s: dict = {}
        s.update(eng)
        # Store each domain's settings under namespaced keys to avoid conflicts
        s["preset"]          = img.get("preset", "balanced")
        s["image_quality"]   = img.get("quality", 85)
        s["strip_metadata"]  = img.get("strip_metadata", False)
        s["resize_max_px"]   = img.get("resize_max_px")
        s["codec"]           = vid.get("codec", "h265")
        s["video_quality"]   = vid.get("quality", 28)
        s["resolution"]      = vid.get("resolution", "original")
        s["fps"]             = vid.get("fps", "original")
        s["skip_hevc"]       = vid.get("skip_hevc", True)
        return s


def _deep_copy(d):
    return json.loads(json.dumps(d))


def _deep_merge(base: dict, override: dict):
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
