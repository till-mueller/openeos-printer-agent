"""Local hardware TSE signing (e.g. Swissbit USB/SD stick).

The stick's own middleware exposes its SE-API (BSI TR-03153 "embedding
interface") as a local RPC server on the host it's plugged into — this
module is the thin client for that RPC, called by the WebSocket handlers in
websocket_client.py when the backend sends a tseSignTransaction /
tseTestConnection / tseExportData job.

IMPORTANT: the request/response shapes below are placeholders. Swissbit's
(or whichever vendor's) actual local RPC schema needs to be filled in against
real hardware + its SDK/docs — this has not been verified against a
provisioned stick. What's real and load-bearing here is the *protocol* on
the backend side (job dispatch over the gateway WebSocket, ack-as-response,
outage handling) — see TseService.recordTransaction on the API for how a
timeout/error here becomes a `tseData.failed: true` marker instead of
blocking the sale.
"""

import base64
import logging

import aiohttp

logger = logging.getLogger(__name__)


class TseSignerError(Exception):
    pass


#: Fields a real signed-transaction response must carry for us to trust it.
#: Without this check, a wrong/mismatched RPC schema could still come back
#: with a 200 and mostly-empty fields, and sign_transaction would report
#: `ok: True` over a fiscally-invalid record instead of failing loudly.
_REQUIRED_SIGN_FIELDS = (
    "transactionNumber",
    "serialNumber",
    "signatureValue",
    "signatureAlgorithm",
)


class TseSigner:
    def __init__(self, rpc_url: str) -> None:
        self._rpc_url = rpc_url.rstrip("/")
        logger.warning(
            "TSE signing is enabled, but this RPC client's request/response "
            "schema has not been verified against real hardware (see the "
            "module docstring in tse_signer.py). Do not rely on it for "
            "production fiscalization until that verification has happened."
        )

    async def sign_transaction(
        self, client_id: str, amount: float, currency: str, payment_method: str
    ) -> dict:
        """Register `client_id` on the stick if needed, then run an
        immediate (start+finish) transaction. Returns the fields
        TseSignTransactionResponse expects on the API side."""
        async with aiohttp.ClientSession() as session:
            # TODO: replace with the real SE-API calls once hardware is
            # available (typically: ensure-client, start-transaction,
            # finish-transaction with amounts-per-vat-rate/payment-type).
            async with session.post(
                f"{self._rpc_url}/client/{client_id}/ensure",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status not in (200, 201):
                    raise TseSignerError(f"ensure-client failed ({resp.status})")

            async with session.post(
                f"{self._rpc_url}/client/{client_id}/tx",
                json={"amount": amount, "currency": currency, "paymentMethod": payment_method},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise TseSignerError(f"sign-transaction failed ({resp.status}): {body}")
                data = await resp.json()

        missing = [f for f in _REQUIRED_SIGN_FIELDS if not data.get(f)]
        if missing:
            # A 200 with an incomplete body means the RPC schema doesn't
            # match what this client expects — surfacing that as a failure
            # (which the API records as a TSE outage) is safer than handing
            # back a "successful" signature that's missing the fields a real
            # receipt/audit would need.
            raise TseSignerError(
                f"sign-transaction response missing required field(s): {', '.join(missing)} "
                "— check the RPC schema against tse_signer.py's expectations"
            )

        return {
            "ok": True,
            "transactionNumber": data.get("transactionNumber"),
            "serialNumber": data.get("serialNumber"),
            "signatureCounter": data.get("signatureCounter"),
            "signatureValue": data.get("signatureValue"),
            "signatureAlgorithm": data.get("signatureAlgorithm"),
            "startTime": data.get("startTime"),
            "endTime": data.get("endTime"),
            "qrCodeData": data.get("qrCodeData"),
        }

    async def test_connection(self) -> dict:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._rpc_url}/status", timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        return {"ok": False, "message": f"TSE-Server antwortet mit {resp.status}"}
                    data = await resp.json()
                    return {"ok": True, "serialNumber": data.get("serialNumber")}
        except Exception as e:  # noqa: BLE001 — surfaced to the admin as-is
            return {"ok": False, "message": str(e)}

    async def export_data(self, client_id: str, period_start: str, period_end: str) -> dict:
        """Pull the TR-03153 TAR export for one client's date range —
        the handover artifact for the weekend-rental tenant model."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._rpc_url}/client/{client_id}/export",
                    params={"periodStart": period_start, "periodEnd": period_end},
                    timeout=aiohttp.ClientTimeout(total=90),
                ) as resp:
                    if resp.status != 200:
                        body = await resp.text()
                        return {"ok": False, "message": f"Export fehlgeschlagen ({resp.status}): {body}"}
                    raw = await resp.read()
            return {
                "ok": True,
                "dataBase64": base64.b64encode(raw).decode("ascii"),
                "filename": f"tse-export-{client_id}-{period_start[:10]}.tar",
            }
        except Exception as e:  # noqa: BLE001
            logger.error(f"TSE export failed for client {client_id}: {e}")
            return {"ok": False, "message": str(e)}
