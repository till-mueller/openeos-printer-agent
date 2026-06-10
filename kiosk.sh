#!/usr/bin/env bash
# OpenEOS Kiosk Display Launcher
# Starts Chromium in kiosk mode pointing to the station display URL.

set -euo pipefail

CONFIG_FILE="${OPENEOS_KIOSK_CONFIG:-/opt/openeos-printer-agent/config/config.yaml}"
DEFAULT_URL="http://localhost:3002/device/station"

# Read display URL from config (simple grep - no yaml parser needed)
if [ -f "$CONFIG_FILE" ]; then
    DISPLAY_URL=$(grep -oP '^\s*display_url:\s*"\K[^"]+' "$CONFIG_FILE" 2>/dev/null \
               || grep -oP "^\s*display_url:\s*'\K[^']+" "$CONFIG_FILE" 2>/dev/null \
               || grep -oP '^\s*display_url:\s*\K\S+' "$CONFIG_FILE" 2>/dev/null \
               || echo "$DEFAULT_URL")
else
    DISPLAY_URL="$DEFAULT_URL"
fi

echo "[OpenEOS Kiosk] Starting display: $DISPLAY_URL"

# Wait for X server / Wayland compositor
for i in $(seq 1 30); do
    if [ -n "${WAYLAND_DISPLAY:-}" ] || [ -n "${DISPLAY:-}" ]; then
        break
    fi
    echo "[OpenEOS Kiosk] Waiting for display server... ($i/30)"
    sleep 2
done

# Disable screen blanking / screensaver
if command -v xset &>/dev/null && [ -n "${DISPLAY:-}" ]; then
    xset s off
    xset -dpms
    xset s noblank
fi

# Hide cursor after 3 seconds of inactivity
if command -v unclutter &>/dev/null; then
    unclutter -idle 3 -root &
fi

# Clear Chromium crash flags (prevents "restore session" popup)
CHROMIUM_DIR="$HOME/.config/chromium"
if [ -d "$CHROMIUM_DIR/Default" ]; then
    sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' "$CHROMIUM_DIR/Default/Preferences" 2>/dev/null || true
    sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' "$CHROMIUM_DIR/Default/Preferences" 2>/dev/null || true
fi

# Launch Chromium in kiosk mode
exec chromium-browser \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --disable-restore-session-state \
    --disable-features=TranslateUI \
    --disable-component-update \
    --check-for-update-interval=31536000 \
    --autoplay-policy=no-user-gesture-required \
    --no-first-run \
    --start-fullscreen \
    --window-position=0,0 \
    "$DISPLAY_URL"
