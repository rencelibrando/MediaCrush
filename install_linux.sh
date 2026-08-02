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

echo "MediaCrush Linux installer"
echo "Source:  $SOURCE_DIR"
echo "Install: $APP_DIR"

install_ffmpeg_if_missing() {
  if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
    echo "FFmpeg found"
    return
  fi

  echo "FFmpeg was not found. Attempting platform package install..."
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is not available. Install ffmpeg manually with your package manager." >&2
    return
  fi

  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg 2>/dev/null || {
      echo "Direct ffmpeg install via dnf failed." >&2
      echo "On Fedora: enable RPM Fusion first:" >&2
      echo "  sudo dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-\$(rpm -E %fedora).noarch.rpm" >&2
      echo "  sudo dnf install -y ffmpeg" >&2
      echo "On RHEL/CentOS: enable EPEL and RPM Fusion first:" >&2
      echo "  sudo dnf install -y epel-release" >&2
      echo "  sudo dnf install -y https://mirrors.rpmfusion.org/free/el/rpmfusion-free-release-\$(rpm -E %rhel).noarch.rpm" >&2
      echo "  sudo dnf install -y ffmpeg" >&2
    }
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y epel-release || true
    sudo yum install -y ffmpeg 2>/dev/null || {
      echo "Direct ffmpeg install via yum failed." >&2
      echo "Enable EPEL and RPM Fusion first, then run: sudo yum install -y ffmpeg" >&2
    }
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --needed ffmpeg
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper install -y ffmpeg
  else
    echo "No supported package manager found. Install ffmpeg manually." >&2
  fi
}

echo_step "[1/6] Checking Python"
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

echo_step "[2/6] Copying application files"
rm -rf "$APP_DIR"
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

echo_step "[3/6] Creating local Python environment"
if ! "$PYTHON3" -m venv "$VENV_DIR"; then
  echo "Could not create a virtual environment." >&2
  echo "Install the python3-venv package for your distribution." >&2
  echo "  Debian/Ubuntu: sudo apt install python3-venv" >&2
  echo "  Fedora/RHEL:   sudo dnf install python3" >&2
  echo "  Arch:          sudo pacman -S python" >&2
  echo "  openSUSE:      sudo zypper install python3-venv" >&2
  exit 1
fi
echo "Virtual environment ready"

echo_step "[4/7] Installing platform media tools"
install_ffmpeg_if_missing

echo_step "[5/7] Running app setup in install folder"
(cd "$APP_DIR" && "$PYTHON_BIN" -c "import main; main.bootstrap(); print('MediaCrush setup complete')")

if ! command -v ffmpeg >/dev/null 2>&1 && [ ! -x "$APP_DIR/.tools/ffmpeg/ffmpeg" ]; then
  echo ""
  echo "FFmpeg was not found. MediaCrush will still open, but video compression needs FFmpeg."
  if command -v apt-get >/dev/null 2>&1; then
    echo "Install it with: sudo apt-get install ffmpeg"
  elif command -v dnf >/dev/null 2>&1; then
    echo "Install it with: sudo dnf install ffmpeg"
    echo "  (On Fedora, enable RPM Fusion first if needed.)"
  elif command -v yum >/dev/null 2>&1; then
    echo "Install it with: sudo yum install ffmpeg"
    echo "  (Ensure EPEL and RPM Fusion are enabled.)"
  elif command -v pacman >/dev/null 2>&1; then
    echo "Install it with: sudo pacman -S ffmpeg"
  else
    echo "Install ffmpeg with your distribution's package manager."
  fi
fi

echo_step "[6/7] Creating launcher"
mkdir -p "$BIN_DIR"
cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
exec "$PYTHON_BIN" "$APP_DIR/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"
echo "Launcher created: $LAUNCHER"

echo_step "[7/7] Creating desktop shortcut"
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
echo "Installation complete."
echo "Launch MediaCrush from the desktop shortcut, app menu, or run:"
echo "  $LAUNCHER"
