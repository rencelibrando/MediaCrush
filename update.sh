#!/usr/bin/env bash
# MediaCrush Linux Auto-Updater
# Automatically syncs local changes or pulls latest updates into ~/.local/share/mediacrush
set -euo pipefail

echo_step() {
  printf '\n\033[36m%s\033[0m\n' "$1"
}

echo_success() {
  printf '\033[32m%s\033[0m\n' "$1"
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

echo "MediaCrush Auto-Updater"
echo "Source:  $SOURCE_DIR"
echo "Target:  $APP_DIR"

if [ ! -d "$APP_DIR" ]; then
  echo "MediaCrush is not installed yet at $APP_DIR."
  echo "Running initial installation via install_linux.sh..."
  exec "$SOURCE_DIR/install_linux.sh"
fi

# Step 1: Optional git pull if requested or flag passed
if [ "${1:-}" = "--pull" ] || [ "${1:-}" = "-p" ]; then
  echo_step "[1/5] Pulling latest code from git repository..."
  if command -v git >/dev/null 2>&1 && [ -d "$SOURCE_DIR/.git" ]; then
    git -C "$SOURCE_DIR" pull --ff-only || {
      echo "Notice: git pull failed or has local modifications; continuing with local files..."
    }
  fi
else
  echo_step "[1/5] Preparing source files"
fi

# Step 2: Sync files to installation folder (preserving .venv and .tools)
echo_step "[2/5] Updating application files in $APP_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '.tools' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '*.pyo' \
    "$SOURCE_DIR"/ "$APP_DIR"/
else
  find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name '.venv' ! -name '.tools' -exec rm -rf {} +
  tar \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='.tools' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    -C "$SOURCE_DIR" -cf - . | tar -C "$APP_DIR" -xf -
fi
echo_success "Files synchronized successfully."

# Step 3: Ensure virtual environment exists and update dependencies
echo_step "[3/5] Updating Python dependencies in virtual environment"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Virtual environment missing; creating at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
fi

echo "Updating pip and dependencies from requirements.txt..."
"$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel --quiet
if [ -f "$APP_DIR/requirements.txt" ]; then
  "$PYTHON_BIN" -m pip install -r "$APP_DIR/requirements.txt" --quiet
fi
echo_success "Dependencies updated."

# Step 4: Ensure launcher and desktop shortcuts exist and are executable
echo_step "[4/5] Verifying launcher and shortcuts"
mkdir -p "$BIN_DIR" "$DESKTOP_DIR" "$APPLICATIONS_DIR"

cat > "$LAUNCHER" <<EOF
#!/usr/bin/env bash
cd "$APP_DIR"
exec "$PYTHON_BIN" "$APP_DIR/main.py" "\$@"
EOF
chmod +x "$LAUNCHER"

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
echo_success "Launchers and shortcuts verified."

# Step 5: Self-test verification
echo_step "[5/5] Running verification self-test"
(cd "$APP_DIR" && "$PYTHON_BIN" -c "import main; main.bootstrap(); print('Installed version verification: OK')")

echo ""
echo_success "MediaCrush was successfully updated!"
echo "You can launch the updated application from your desktop shortcut, app menu, or by running: mediacrush"
