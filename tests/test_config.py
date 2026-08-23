import pytest
from pydantic import ValidationError

from src.config import AppConfig, PrinterConfig, ServerConfig


class TestServerConfig:
    def test_valid_config(self, sample_server_config):
        assert sample_server_config.url == "http://localhost:3000"
        assert sample_server_config.device_token == "test-token-123"
        assert sample_server_config.heartbeat_interval_ms == 30000

    def test_heartbeat_interval_seconds(self, sample_server_config):
        assert sample_server_config.heartbeat_interval == 30.0

    def test_reconnect_interval_seconds(self, sample_server_config):
        assert sample_server_config.reconnect_interval == 5.0

    def test_device_token_is_optional(self):
        # No device_token -> self-registration mode (see DeviceRegistrar),
        # not a validation error. A prior version of this test asserted the
        # opposite; device_token has been optional since self-registration
        # was added.
        config = ServerConfig(url="http://localhost:3000")
        assert config.device_token is None


class TestPrinterConfig:
    def test_valid_network_printer(self, sample_printer_config):
        assert sample_printer_config.connectionType == "network"
        assert sample_printer_config.ipAddress == "192.168.1.100"
        assert sample_printer_config.paperWidth == 80

    def test_valid_usb_printer(self, sample_usb_printer_config):
        assert sample_usb_printer_config.connectionType == "usb"
        assert sample_usb_printer_config.usbVendorId == "0x04b8"

    def test_invalid_connection_type(self):
        with pytest.raises(ValidationError, match="connectionType"):
            PrinterConfig(
                localId="p1",
                name="Bad Printer",
                connectionType="serial",
            )

    def test_invalid_paper_width(self):
        with pytest.raises(ValidationError, match="paperWidth"):
            PrinterConfig(
                localId="p1",
                name="Bad Printer",
                connectionType="network",
                paperWidth=72,
            )

    def test_default_paper_width(self):
        cfg = PrinterConfig(localId="p1", name="P", connectionType="usb")
        assert cfg.paperWidth == 80

    def test_58mm_paper(self):
        cfg = PrinterConfig(localId="p1", name="P", connectionType="usb", paperWidth=58)
        assert cfg.paperWidth == 58


class TestAppConfig:
    def test_full_config(self, sample_config):
        assert sample_config.agent.id == "test-agent"
        assert len(sample_config.printers) == 1
        assert sample_config.printers[0].name == "Test Printer"

    def test_defaults(self):
        cfg = AppConfig(
            server=ServerConfig(url="http://localhost:3000", device_token="tok"),
        )
        assert cfg.agent.id == "agent-01"
        assert cfg.logging.level == "INFO"
        assert cfg.local_server.enabled is True
        assert cfg.sentry.enabled is False

    def test_no_printers(self):
        cfg = AppConfig(
            server=ServerConfig(url="http://localhost:3000", device_token="tok"),
        )
        assert cfg.printers == []
