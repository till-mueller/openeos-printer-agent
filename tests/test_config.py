import pytest
from pydantic import ValidationError

from src.config import AppConfig, ServerConfig, PrinterConfig, AgentConfig


class TestServerConfig:
    def test_valid_config(self, sample_server_config):
        assert sample_server_config.url == "http://localhost:3000"
        assert sample_server_config.device_token == "test-token-123"
        assert sample_server_config.heartbeat_interval_ms == 30000

    def test_heartbeat_interval_seconds(self, sample_server_config):
        assert sample_server_config.heartbeat_interval == 30.0

    def test_reconnect_interval_seconds(self, sample_server_config):
        assert sample_server_config.reconnect_interval == 5.0

    def test_missing_device_token(self):
        with pytest.raises(ValidationError):
            ServerConfig(url="http://localhost:3000")


class TestPrinterConfig:
    def test_valid_network_printer(self, sample_printer_config):
        assert sample_printer_config.connection_type == "network"
        assert sample_printer_config.ip_address == "192.168.1.100"
        assert sample_printer_config.paper_width == 80

    def test_valid_usb_printer(self, sample_usb_printer_config):
        assert sample_usb_printer_config.connection_type == "usb"
        assert sample_usb_printer_config.usb_vendor_id == "0x04b8"

    def test_invalid_connection_type(self):
        with pytest.raises(ValidationError, match="connection_type"):
            PrinterConfig(
                id="p1",
                name="Bad Printer",
                connection_type="serial",
            )

    def test_invalid_paper_width(self):
        with pytest.raises(ValidationError, match="paper_width"):
            PrinterConfig(
                id="p1",
                name="Bad Printer",
                connection_type="network",
                paper_width=72,
            )

    def test_default_paper_width(self):
        cfg = PrinterConfig(id="p1", name="P", connection_type="usb")
        assert cfg.paper_width == 80

    def test_58mm_paper(self):
        cfg = PrinterConfig(id="p1", name="P", connection_type="usb", paper_width=58)
        assert cfg.paper_width == 58


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
