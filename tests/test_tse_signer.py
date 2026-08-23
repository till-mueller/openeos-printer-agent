"""Tests for tse_signer.py's local SE-API RPC client.

Mocks aiohttp.ClientSession.post/get directly rather than pulling in a
response-mocking library (aioresponses 0.7.9 doesn't support aiohttp's
current ClientResponse signature — see the internal TypeError it raises
constructing a response) — plain unittest.mock avoids that version coupling.
"""

import base64

import aiohttp
import pytest
from unittest.mock import MagicMock, patch

from src.tse_signer import TseSigner, TseSignerError

RPC_URL = "http://localhost:8998"


class _FakeResponse:
    def __init__(self, status=200, json_data=None, text_data="", read_data=b""):
        self.status = status
        self._json = json_data
        self._text = text_data
        self._read = read_data

    async def json(self):
        return self._json

    async def text(self):
        return self._text

    async def read(self):
        return self._read


class _FakeRequestCM:
    """Stands in for aiohttp's _RequestContextManager: `session.post(...)`
    returns this (synchronously), and `async with` enters/exits it."""

    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, *exc_info):
        return False


def _mock_calls(*responses):
    """MagicMock usable as session.post/get: each call consumes the next
    fake response in order (ensure-client, then sign-transaction, etc.)."""
    return MagicMock(side_effect=[_FakeRequestCM(r) for r in responses])


@pytest.fixture
def signer():
    return TseSigner(RPC_URL)


class TestSignTransaction:
    async def test_success(self, signer):
        ensure_resp = _FakeResponse(status=200)
        tx_resp = _FakeResponse(
            status=200,
            json_data={
                "transactionNumber": 42,
                "serialNumber": "SN-1",
                "signatureCounter": 7,
                "signatureValue": "sig-abc",
                "signatureAlgorithm": "ecdsa-plain-SHA256",
                "startTime": "2026-08-23T10:00:00Z",
                "endTime": "2026-08-23T10:00:01Z",
                "qrCodeData": "V0;client-1;42;...",
            },
        )
        with patch.object(aiohttp.ClientSession, "post", _mock_calls(ensure_resp, tx_resp)):
            result = await signer.sign_transaction(
                client_id="client-1", amount=12.5, currency="EUR", payment_method="cash"
            )

        assert result["ok"] is True
        assert result["transactionNumber"] == 42
        assert result["signatureValue"] == "sig-abc"
        assert result["qrCodeData"] == "V0;client-1;42;..."

    async def test_ensure_client_failure_raises(self, signer):
        ensure_resp = _FakeResponse(status=500)
        with patch.object(aiohttp.ClientSession, "post", _mock_calls(ensure_resp)):
            with pytest.raises(TseSignerError):
                await signer.sign_transaction(
                    client_id="client-1", amount=12.5, currency="EUR", payment_method="cash"
                )

    async def test_transaction_failure_raises(self, signer):
        ensure_resp = _FakeResponse(status=200)
        tx_resp = _FakeResponse(status=500, text_data="hardware error")
        with patch.object(aiohttp.ClientSession, "post", _mock_calls(ensure_resp, tx_resp)):
            with pytest.raises(TseSignerError, match="hardware error"):
                await signer.sign_transaction(
                    client_id="client-1", amount=12.5, currency="EUR", payment_method="cash"
                )


class TestConnection:
    async def test_success(self, signer):
        resp = _FakeResponse(status=200, json_data={"serialNumber": "SN-1"})
        with patch.object(aiohttp.ClientSession, "get", _mock_calls(resp)):
            result = await signer.test_connection()

        assert result == {"ok": True, "serialNumber": "SN-1"}

    async def test_non_200_reports_not_ok(self, signer):
        resp = _FakeResponse(status=503)
        with patch.object(aiohttp.ClientSession, "get", _mock_calls(resp)):
            result = await signer.test_connection()

        assert result["ok"] is False
        assert "503" in result["message"]

    async def test_unreachable_agent_reports_not_ok(self, signer):
        # Simulates the TSE middleware being offline/unreachable.
        with patch.object(
            aiohttp.ClientSession,
            "get",
            MagicMock(side_effect=aiohttp.ClientConnectionError("connection refused")),
        ):
            result = await signer.test_connection()

        assert result["ok"] is False
        assert "connection refused" in result["message"]


class TestExportData:
    async def test_success_returns_base64_payload(self, signer):
        raw = b"fake-tar-archive-bytes"
        resp = _FakeResponse(status=200, read_data=raw)
        with patch.object(aiohttp.ClientSession, "get", _mock_calls(resp)):
            result = await signer.export_data(
                client_id="client-1", period_start="2026-08-21", period_end="2026-08-23"
            )

        assert result["ok"] is True
        assert base64.b64decode(result["dataBase64"]) == raw
        assert result["filename"] == "tse-export-client-1-2026-08-21.tar"

    async def test_failure_reports_not_ok(self, signer):
        resp = _FakeResponse(status=500, text_data="export job failed")
        with patch.object(aiohttp.ClientSession, "get", _mock_calls(resp)):
            result = await signer.export_data(
                client_id="client-1", period_start="2026-08-21", period_end="2026-08-23"
            )

        assert result["ok"] is False
        assert "export job failed" in result["message"]
