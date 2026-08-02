# MediaCrush 

A centralized media compression application .

## Features

- **Drag & drop** files or folders (recursive scanning)
- **Image compression** — JPG, PNG, WEBP, HEIC, BMP, TIFF, GIF, AVIF
- **Video compression** — MP4, MKV, AVI, MOV, WEBM, FLV, WMV, M4V, MPEG
- **GPU acceleration** — AMD VAAPI (Linux), NVIDIA NVENC (Linux/Windows), Intel QSV (Linux), DirectX D3D11VA (Windows) (auto-detected)
- **Dual CPU+GPU** — Auto-detected optimal worker counts based on your hardware
- **Dark / Light theme** toggle
- **Presets** — Lossless, High, Balanced, Small, Tiny
- **Real-time progress** per file + overall
- **Stats dashboard** — saved space, ETA, before/after
- **Logs viewer** with color-coded output + export
- **Settings persist** across sessions

## Quick Start

### Linux

**Automatic Installation (Recommended):**

```bash
# 1. Clone the repository
git clone https://github.com/rencelibrando/MediaCrush.git
cd MediaCrush

# 2. Run the installer
chmod +x install_linux.sh
./install_linux.sh
```

The installer does everything for you:
- **Copies the app** to a permanent folder: `~/.local/share/mediacrush`
- **Creates a Python virtual environment** and installs `requirements.txt`
- **Installs FFmpeg** if missing (prompts for sudo; on Fedora it may ask you to enable RPM Fusion first)
- **Creates a launcher** at `~/.local/bin/mediacrush`
- **Creates a desktop shortcut** on your Desktop and in the app menu

```bash
# 3. Launch
mediacrush
# or click the MediaCrush desktop/app-menu icon
```

**Manual Installation:**

```bash
# 1. Install Python 3.8+ and FFmpeg (required for video compression)
# Debian/Ubuntu:
sudo apt install python3 python3-venv ffmpeg
# Fedora/RHEL:
sudo dnf install python3
#   FFmpeg on Fedora usually needs RPM Fusion first:
sudo dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm
sudo dnf install -y ffmpeg

# 2. Create a virtual environment and install dependencies
cd MediaCrush
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Install xcb-cursor for GUI display
# Debian/Ubuntu:
sudo apt install libxcb-cursor0
# Fedora/RHEL:
sudo dnf install xcb-util-cursor
# Arch:
sudo pacman -S libxcb

# 4. Run
python main.py
```

### Windows

**Automatic Installation (Recommended):**

```powershell
# Right-click on install_windows.ps1 and select "Run with PowerShell"
# Or run in PowerShell as Administrator:
.\install_windows.ps1
```

**Manual Installation:**

```bash
# 1. Install Python 3.8+ from python.org

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install FFmpeg (required for video compression)
#    Download from: https://ffmpeg.org/download.html
#    Add ffmpeg.exe to your PATH

# 4. Run
python main.py
```

**Note:** GPU acceleration on Windows uses DirectX (D3D11VA) for AMD/Intel GPUs and NVENC for NVIDIA GPUs. These are auto-detected.

## Project Structure

```
MediaCrush/
├── main.py                    # Entry point
├── requirements.txt
├── core/
│   ├── task.py                # Task data model
│   ├── hardware.py            # GPU detection (VAAPI/NVENC/QSV)
│   ├── image_compressor.py    # Pillow-based image compression
│   ├── video_compressor.py    # FFmpeg video compression
│   └── engine.py              # Thread pool engine + Qt signals
├── config/
│   └── settings.py            # JSON config (~/.config/mediacrush/)
├── utils/
│   └── logger.py              # In-memory + file logger
└── gui/
    ├── main_window.py         # Main application window
    ├── styles.py              # QSS dark/light themes
    ├── widgets/
    │   ├── drop_zone.py       # Drag & drop widget
    │   ├── queue_widget.py    # Per-task progress rows
    │   ├── stats_widget.py    # Live stats dashboard
    │   └── logs_widget.py     # Logs viewer dialog
    └── dialogs/
        └── settings_dialog.py # Settings panel
```

## Settings (persisted at `~/.config/mediacrush/settings.json`)

| Category | Key             | Default    | Description                   |
|----------|-----------------|------------|-------------------------------|
| Image    | preset          | balanced   | lossless/high/balanced/small/tiny |
| Image    | quality         | 85         | JPEG/WebP quality (1–100)     |
| Image    | strip_metadata  | false      | Remove EXIF data              |
| Video    | codec           | h265       | h264 / h265 / av1             |
| Video    | quality         | 28         | CRF/QP (lower = better)       |
| Video    | skip_hevc       | true       | Skip already-HEVC files       |
| Engine   | gpu_workers     | 4          | Parallel GPU encodes          |
| Engine   | cpu_workers     | 8          | Parallel CPU encodes          |
| Engine   | output_mode     | inplace    | inplace / alongside / custom  |
