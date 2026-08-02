#!/usr/bin/env python3
"""MediaCrush entry point with first-run setup checks."""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from utils.process import hidden_subprocess_kwargs


ROOT = Path(__file__).resolve().parent
TOOLS_DIR = ROOT / ".tools"
FFMPEG_DIR = TOOLS_DIR / "ffmpeg"

REQUIRED_IMPORTS = {
    "PySide6": "PySide6>=6.5.0",
    "PIL": "Pillow>=10.0.0",
    "pillow_heif": "pillow-heif>=0.13.0",
    "psutil": "psutil>=5.9.0",
}


def _run_setup_cmd(cmd: list[str], timeout: int | None = None) -> None:
    subprocess.check_call(
        cmd, cwd=str(ROOT), timeout=timeout, **hidden_subprocess_kwargs()
    )


def _missing_python_requirements() -> list[str]:
    return [
        requirement
        for module_name, requirement in REQUIRED_IMPORTS.items()
        if importlib.util.find_spec(module_name) is None
    ]


def _ensure_python_dependencies() -> None:
    missing = _missing_python_requirements()
    if not missing:
        return

    print("MediaCrush setup: installing missing Python dependencies...")
    _run_setup_cmd([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

    requirements = ROOT / "requirements.txt"
    if requirements.exists():
        _run_setup_cmd([sys.executable, "-m", "pip", "install", "-r", str(requirements)])
    else:
        _run_setup_cmd([sys.executable, "-m", "pip", "install", *missing])


def _prepend_path(path: Path) -> None:
    os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _install_windows_ffmpeg() -> None:
    ffmpeg_exe = FFMPEG_DIR / "ffmpeg.exe"
    ffprobe_exe = FFMPEG_DIR / "ffprobe.exe"
    if ffmpeg_exe.exists() and ffprobe_exe.exists():
        _prepend_path(FFMPEG_DIR)
        return

    print("MediaCrush setup: installing local FFmpeg for Windows...")
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

    with tempfile.TemporaryDirectory(prefix="mediacrush-ffmpeg-") as tmp:
        tmp_dir = Path(tmp)
        archive = tmp_dir / "ffmpeg.zip"
        extract_dir = tmp_dir / "extract"
        urllib.request.urlretrieve(url, archive)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_dir)

        bins = sorted(extract_dir.glob("*/bin"))
        if not bins or not (bins[0] / "ffmpeg.exe").exists():
            raise RuntimeError("FFmpeg archive did not contain ffmpeg.exe")

        if FFMPEG_DIR.exists():
            shutil.rmtree(FFMPEG_DIR)
        shutil.copytree(bins[0], FFMPEG_DIR)

    _prepend_path(FFMPEG_DIR)


def _ensure_ffmpeg() -> None:
    local_ffmpeg = FFMPEG_DIR / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    local_ffprobe = FFMPEG_DIR / ("ffprobe.exe" if os.name == "nt" else "ffprobe")

    if local_ffmpeg.exists() and local_ffprobe.exists():
        _prepend_path(FFMPEG_DIR)
        return

    if _ffmpeg_available():
        return

    if os.name == "nt":
        _install_windows_ffmpeg()
        return

    print(
        "MediaCrush setup warning: FFmpeg was not found. "
        "Install ffmpeg with your system package manager for video compression."
    )


def bootstrap() -> None:
    sys.path.insert(0, str(ROOT))
    _ensure_python_dependencies()
    _ensure_ffmpeg()


def main() -> None:
    bootstrap()

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QFont

    from config.settings import Settings
    from gui.main_window import MainWindow
    from gui.styles import get_style

    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("MediaCrush")
    app.setOrganizationName("MediaCrush")
    app.setApplicationVersion("1.0.0")

    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(font)

    settings = Settings()
    app.setStyleSheet(get_style(settings.get("ui.theme", "dark")))

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
