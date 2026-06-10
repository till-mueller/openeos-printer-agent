import pytest

from src.config import AppConfig, AgentConfig, ServerConfig, PrinterConfig, LoggingConfig, LocalServerConfig, SentryConfig


@pytest.fixture
def sample_server_config():
    return ServerConfig(
        url="http://localhost:3000",
        device_token="test-token-123",
    )


@pytest.fixture
def sample_printer_config():
    return PrinterConfig(
        id="printer-001",
        name="Test Printer",
        connection_type="network",
        paper_width=80,
        ip_address="192.168.1.100",
        port=9100,
    )


@pytest.fixture
def sample_usb_printer_config():
    return PrinterConfig(
        id="printer-002",
        name="USB Printer",
        connection_type="usb",
        paper_width=80,
        usb_vendor_id="0x04b8",
        usb_product_id="0x0202",
    )


@pytest.fixture
def sample_config(sample_server_config, sample_printer_config):
    return AppConfig(
        agent=AgentConfig(id="test-agent", name="Test Agent"),
        server=sample_server_config,
        printers=[sample_printer_config],
        logging=LoggingConfig(level="DEBUG"),
        local_server=LocalServerConfig(enabled=False),
        sentry=SentryConfig(enabled=False),
    )


@pytest.fixture
def sample_print_job():
    return {
        "jobId": "job-001",
        "printerId": "printer-001",
        "templateName": "receipt",
        "copies": 1,
        "payload": {
            "organization": {"name": "Test Verein"},
            "order_number": "42",
            "created_at": "2024-06-15T14:30:00Z",
            "items": [
                {"quantity": 2, "name": "Bratwurst", "total": 7.00},
                {"quantity": 1, "name": "Cola 0.5l", "total": 3.50},
            ],
            "total": 10.50,
            "payment_method": "Bar",
            "paid_amount": 20.00,
            "change": 9.50,
        },
    }


@pytest.fixture
def sample_kitchen_job():
    return {
        "jobId": "job-002",
        "printerId": "printer-001",
        "templateName": "kitchen",
        "payload": {
            "order_number": "42",
            "daily_number": 42,
            "table_number": "5",
            "created_at": "2024-06-15T14:30:00Z",
            "items": [
                {"quantity": 2, "name": "Bratwurst", "notes": "ohne Senf"},
                {"quantity": 1, "name": "Pommes", "kitchen_notes": "extra knusprig"},
            ],
        },
    }
