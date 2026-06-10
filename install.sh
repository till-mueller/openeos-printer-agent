#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/openeos-printer-agent"
SERVICE_NAME="openeos-printer"
SERVICE_USER="openeos"
LOG_DIR="/var/log/openeos-printer"

echo "============================================"
echo "  OpenEOS Printer Agent - Installation"
echo "============================================"
echo ""

# Check root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo)."
    exit 1
fi

# 1. Install system dependencies
echo "[1/7] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip libusb-1.0-0-dev libjpeg-dev

# 2. Create system user
echo "[2/7] Creating system user..."
if ! id -u "$SERVICE_USER" &>/dev/null; then
    useradd --system --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
    echo "  Created user: $SERVICE_USER"
else
    echo "  User $SERVICE_USER already exists"
fi
usermod -aG lp,plugdev "$SERVICE_USER" 2>/dev/null || true

# 3. Copy files
echo "[3/7] Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r src templates config requirements.txt "$INSTALL_DIR/"
mkdir -p "$INSTALL_DIR/cache/templates"
mkdir -p "$LOG_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR" "$LOG_DIR"

# 4. Python virtual environment
echo "[4/7] Setting up Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/requirements.txt"

# 5. udev rules for USB thermal printers
echo "[5/7] Installing udev rules..."
cat > /etc/udev/rules.d/99-openeos-printer.rules << 'UDEV'
# Epson TM series
SUBSYSTEM=="usb", ATTR{idVendor}=="04b8", MODE="0666", GROUP="plugdev"
# Star Micronics
SUBSYSTEM=="usb", ATTR{idVendor}=="0519", MODE="0666", GROUP="plugdev"
# Bixolon
SUBSYSTEM=="usb", ATTR{idVendor}=="1504", MODE="0666", GROUP="plugdev"
# Custom (Italy)
SUBSYSTEM=="usb", ATTR{idVendor}=="0dd4", MODE="0666", GROUP="plugdev"
UDEV
udevadm control --reload-rules
udevadm trigger

# 6. Install systemd service
echo "[6/7] Installing systemd service..."
cp openeos-printer.service /etc/systemd/system/${SERVICE_NAME}.service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# 7. Done
echo "[7/7] Installation complete!"
echo ""
echo "============================================"
echo "  Next steps:"
echo "============================================"
echo ""
echo "  1. Copy and edit the configuration:"
echo "     cp $INSTALL_DIR/config/config.example.yaml $INSTALL_DIR/config/config.yaml"
echo "     nano $INSTALL_DIR/config/config.yaml"
echo ""
echo "  2. Set the device_token from the OpenEOS admin panel"
echo ""
echo "  3. Start the service:"
echo "     sudo systemctl start $SERVICE_NAME"
echo ""
echo "  4. Check status:"
echo "     sudo systemctl status $SERVICE_NAME"
echo "     sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  5. Open status page: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
