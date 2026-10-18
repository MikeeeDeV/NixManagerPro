#!/usr/bin/env bash
# ==============================================================================
# NixManager Pro — Desktop Integration Installer
# Installs .desktop launcher into user applications directory (~/.local/share/applications)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.local/share/applications"
TARGET_FILE="${TARGET_DIR}/nixmanager.desktop"

echo "❄️  Installing NixManager Pro Desktop Integration..."

# Detect Python interpreter (prefer project venv)
if [ -f "${SCRIPT_DIR}/.venv/bin/python" ]; then
    PYTHON_EXEC="${SCRIPT_DIR}/.venv/bin/python"
else
    PYTHON_EXEC="$(which python3)"
fi

APP_MAIN="${SCRIPT_DIR}/main.py"
ICON_PATH="${SCRIPT_DIR}/assets/nixmanager.svg"

# Ensure target applications directory exists
mkdir -p "${TARGET_DIR}"

# Process template
sed \
    -e "s|@PYTHON_EXEC@|${PYTHON_EXEC}|g" \
    -e "s|@APP_MAIN@|${APP_MAIN}|g" \
    -e "s|@ICON_PATH@|${ICON_PATH}|g" \
    "${SCRIPT_DIR}/assets/nixmanager.desktop.template" > "${TARGET_FILE}"

chmod +x "${TARGET_FILE}"
chmod +x "${APP_MAIN}"

# Update desktop database if available
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${TARGET_DIR}" || true
fi

echo "✅ Desktop launcher installed to: ${TARGET_FILE}"
echo "🎉 NixManager Pro is now available in your Ubuntu Application Launcher / Dash!"
