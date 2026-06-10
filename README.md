# OpenEOS Printer Agent

Python-based agent that runs on a Raspberry Pi (or any Linux machine) to control ESC/POS thermal printers via WebSocket communication with the OpenEOS backend.

## Features

- Multi-printer support (USB, Network, Bluetooth)
- Real-time print job reception via Socket.io
- Jinja2 template engine with server-side template override
- Per-printer job queues with retry logic
- Local status web server (http://localhost:8080)
- Heartbeat monitoring with system metrics
- Systemd service with security hardening

## Requirements

- Python 3.11+
- Raspberry Pi OS / Debian / Ubuntu
- ESC/POS compatible thermal printer

## Quick Start

### Raspberry Pi Installation

```bash
# Clone the repository
git clone https://github.com/openeos/openeos-printer-agent.git
cd openeos-printer-agent

# Run the installer (as root)
sudo ./install.sh

# Configure
sudo cp /opt/openeos-printer-agent/config/config.example.yaml \
        /opt/openeos-printer-agent/config/config.yaml
sudo nano /opt/openeos-printer-agent/config/config.yaml

# Start
sudo systemctl start openeos-printer
sudo systemctl status openeos-printer
```

### Docker

```bash
docker build -t openeos-printer-agent .
docker run -d \
  --name openeos-printer \
  -v ./config/config.yaml:/app/config/config.yaml:ro \
  -p 8080:8080 \
  --device /dev/usb/lp0 \
  openeos-printer-agent
```

### Development

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy and edit config
cp config/config.example.yaml config/config.yaml

# Run
python -m src.main --config config/config.yaml

# Run tests
pytest tests/
```

## Configuration

See `config/config.example.yaml` for all options. Key settings:

| Setting | Description |
|---------|-------------|
| `server.url` | OpenEOS API server URL |
| `server.device_token` | Device authentication token (from admin panel) |
| `printers[].connection_type` | `usb`, `network`, or `bluetooth` |
| `printers[].paper_width` | `80` (80mm) or `58` (58mm) |

## Architecture

```
┌─────────────────────────────────────────────┐
│            OpenEOS Backend (NestJS)          │
│    Socket.io  ──────────────────────────     │
└─────────┬──────────────────────┬────────────┘
          │ printerJob           │ printerHeartbeat
          │ printerJobComplete   │ printerJobFailed
          ▼                      ▲
┌─────────────────────────────────────────────┐
│          Printer Agent (Python)              │
│                                              │
│  WebSocketClient ──► JobQueue ──► Renderer   │
│       │                  │           │       │
│  SystemMonitor     TemplateEngine  ESC/POS   │
│       │                              │       │
│  LocalServer                     Printer(s)  │
└─────────────────────────────────────────────┘
```

## Status Page

Access `http://<agent-ip>:8080` for a real-time status page showing:
- Server connection status
- Printer statuses with color indicators
- Queue statistics
- System metrics (CPU, memory, disk, network)

## Troubleshooting

### Printer not detected (USB)

```bash
# Check USB devices
lsusb | grep -i epson

# Check permissions
ls -la /dev/usb/lp*

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Service won't start

```bash
# Check logs
sudo journalctl -u openeos-printer -n 50

# Test config
python -m src.main --config config/config.yaml
```

### Connection issues

- Verify `device_token` in config matches the token in the OpenEOS admin panel
- Check network connectivity to the API server
- Check the status page at http://localhost:8080

## Supported Printers

| Brand | Models | Connection |
|-------|--------|-----------|
| Epson | TM-T20III, TM-T88V/VI, TM-M30 | USB, Network |
| Star | TSP143III, TSP654II | USB, Network |
| Bixolon | SRP-350III, SRP-380 | USB, Network |
