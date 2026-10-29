#!/usr/bin/env bash
set -euo pipefail

echo_step() {
  printf '\n\033[36m%s\033[0m\n' "$1"
}

SOURCE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/mediacrush"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="${XDG_DESKTOP_DIR:-$HOME/Desktop}"
APPLICATIONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"
LAUNCHER="$BIN_DIR/mediacrush"
DESKTOP_FILE="$DESKTOP_DIR/MediaCrush.desktop"
APP_DESKTOP_FILE="$APPLICATIONS_DIR/mediacrush.desktop"

echo "MediaCrush Linux Installer"
echo "Source:  $SOURCE_DIR"
echo "Install: $APP_DIR"

install_system_dependencies() {
  echo_step "[1/7] Checking and installing system dependencies (FFmpeg & codecs)"

  # Check if FFmpeg with full codec support already exists
  if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
    if ffmpeg -encoders 2>/dev/null | grep -qE "libx265|libx264"; then
      echo "FFmpeg with full H.264/H.265 codec support is already installed."
      return 0
    fi
    echo "Notice: Installed FFmpeg lacks libx264/libx265 encoders (common with Fedora ffmpeg-free)."
  fi

  if ! command -v sudo >/dev/null 2>&1; then
    echo "Warning: sudo is not available. Please install FFmpeg and codecs manually." >&2
    return 0
  fi

  echo "Installing required system packages (may prompt for sudo password)..."

  if command -v dnf >/dev/null 2>&1; then
    echo "Fedora / RHEL detected (dnf)..."
    # Enable RPM Fusion if missing for complete codec support
    if ! dnf repolist 2>/dev/null | grep -q "rpmfusion-free"; then
      echo "Enabling RPM Fusion repositories for complete video codec support..."
      sudo dnf install -y \
        https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm \
        https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm || true
    fi

    # Replace ffmpeg-free with full ffmpeg (including libx264/libx265)
    if rpm -q ffmpeg-free >/dev/null 2>&1; then
      echo "Swapping ffmpeg-free with full ffmpeg (libx264/libx265)..."
      sudo dnf swap -y ffmpeg-free ffmpeg --allowerasing || sudo dnf install -y ffmpeg ffmpeg-libs --allowerasing || true
    else
      echo "Installing full ffmpeg..."
      sudo dnf install -y ffmpeg ffmpeg-libs --allowerasing 2>/dev/null || sudo dnf install -y ffmpeg || true
    fi

    # Install freeworld VAAPI drivers for AMD/Intel GPU hardware acceleration if applicable
    if rpm -q mesa-va-drivers >/dev/null 2>&1 && ! rpm -q mesa-va-drivers-freeworld >/dev/null 2>&1; then
      echo "Installing freeworld VAAPI drivers for GPU hardware acceleration..."
      sudo dnf swap -y mesa-va-drivers mesa-va-drivers-freeworld --allowerasing 2>/dev/null || true
    fi

    # Ensure required runtime libraries are present
    sudo dnf install -y python3-pip python3-devel libglvnd-glx libxkbcommon fontconfig 2>/dev/null || true

  elif command -v apt-get >/dev/null 2>&1; then
    echo "Debian / Ubuntu detected (apt)..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg python3-venv python3-pip libgl1 libegl1 libxkbcommon-x11-0 libfontconfig1 || true

  elif command -v pacman >/dev/null 2>&1; then
    echo "Arch Linux detected (pacman)..."
    sudo pacman -Sy --needed --noconfirm ffmpeg python python-pip libglvnd libxkbcommon fontconfig || true

  elif command -v zypper >/dev/null 2>&1; then
    echo "openSUSE detected (zypper)..."
    sudo zypper install -y ffmpeg python3 python3-pip libglvnd libxkbcommon0 || true

  else
    echo "No supported package manager found (dnf/apt/pacman/zypper). Please install ffmpeg manually." >&2
  fi
}

# Step 1: System packages & FFmpeg
install_system_dependencies

# Step 2: Check Python
echo_step "[2/7] Checking Python version"
if command -v python3 >/dev/null 2>&1; then
  PYTHON3="$(command -v python3)"
else
  echo "Python 3.8+ was not found. Install python3 and python3-venv with your package manager." >&2
  exit 1
fi
"$PYTHON3" - <<'PY'
import sys
if sys.version_info < (3, 8):
    raise SystemExit("Python 3.8+ is required")
PY
echo "Python found: $PYTHON3"

# Step 3: Copy app files
echo_step "[3/7] Copying application files"
mkdir -p "$APP_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '.tools' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.pyo' \
    "$SOURCE_DIR"/ "$APP_DIR"/
else
  find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name '.venv' -exec rm -rf {} +
  tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='.tools' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    -C "$SOURCE_DIR" -cf - . | tar -C "$APP_DIR" -xf -
fi
echo "Application copied to $APP_DIR"

# Step 4: Virtual environment
echo_step "[4/7] Ensuring local Python virtual environment"
if [ ! -d "$VENV_DIR" ] || [ ! -x "$PYTHON_BIN" ]; then
  if ! "$PYTHON3" -m venv "$VENV_DIR"; then
    echo "Could not create a virtual environment." >&2
    echo "Install the python3-venv package for your distribution." >&2
    exit 1
  fi
  echo "Created fresh virtual environment at $VENV_DIR"
else
  echo "Using existing virtual environment at $VENV_DIR"
fi

# Step 5: Install Python dependencies
echo_step "[5/7] Installing all required Python dependencies"
echo "Upgrading pip, setuptools, and wheel..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel

if [ -f "$APP_DIR/requirements.txt" ]; then
  echo "Installing packages from requirements.txt..."
  "$PYTHON_BIN" -m pip install -r "$APP_DIR/requirements.txt"
else
  echo "Installing default packages..."
  "$PYTHON_BIN" -m pip install "PySide6>=6.5.0" "Pillow>=10.0.0" "pillow-heif>=0.13.0" "psutil>=5.9.0" "pynvml>=11.5.0" "pytest>=7.0.0"
fi
echo "Python dependencies installed successfully"

# Step 6: Verify setup
echo_step "[6/7] Verifying application setup"
(cd "$APP_DIR" && "$PYTHON_BIN" -c "import main; main.bootstrap(); print('MediaCrush setup verified successfully')")

# Step 7: Create launcher and desktop shortcuts
echo_step "[7/7] Creating desktop launcher and shortcuts"
mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
exec "$PYTHON_BIN" "$APP_DIR/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"
echo "Launcher created: $LAUNCHER"

mkdir -p "$DESKTOP_DIR" "$APPLICATIONS_DIR"
cat > "$APP_DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=MediaCrush
Comment=Media compression tool
Exec=$LAUNCHER
Path=$APP_DIR
Terminal=false
Categories=AudioVideo;Utility;
EOF
cp "$APP_DESKTOP_FILE" "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE" "$APP_DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPLICATIONS_DIR" >/dev/null 2>&1 || true
fi

echo ""
echo "Installation complete!"
echo "You can launch MediaCrush from the desktop shortcut, application menu, or by running:"
echo "  $LAUNCHER"
