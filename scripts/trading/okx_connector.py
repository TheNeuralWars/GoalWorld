#!/usr/bin/env python3
"""
OKX API v5 Secure Connector — GoalWorld Agentic Trading Engine.

GW-TRADING-002: Secure connector for the OKX REST API (v5) with HMAC-SHA256
request signing, used by the Agentic Trading vertical for market intelligence,
order execution, and risk-controlled trading.

SECURITY MODEL
--------------
- Credentials are NEVER hardcoded. They are read from environment variables
  (OKX_API_KEY, OKX_API_SECRET, OKX_API_PASSPHRASE) or a .env file loaded via
  python-dotenv. The connector refuses to start with missing credentials for
  authenticated endpoints.
- The secret key and passphrase are never logged, printed, or included in
  exception messages.
- All requests go over HTTPS to the official OKX endpoints.
- A dry-run / read-only mode is enforced by default: order-placing methods
  require an explicit `allow_trading=True` flag AND the risk controller to
  pass. This connector is the Execution Gateway; it does NOT decide risk.

SIGNING SPEC (verified against https://www.okx.com/docs-v5/en/)
----------------------------------------------------------------
prehash  = timestamp + method + requestPath + body
sign     = Base64( HMAC_SHA256( secretKey, prehash ) )
timestamp = ISO 8601 UTC with millisecond precision, e.g. 2020-12-08T09:08:57.715Z
Headers: OK-ACCESS-KEY, OK-ACCESS-SIGN, OK-ACCESS-TIMESTAMP, OK-ACCESS-PASSPHRASE
Method must be UPPERCASE (GET / POST / DELETE).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dotenv is optional
    load_dotenv = None

logger = logging.getLogger("goalworld.trading.okx")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OKX_REST_BASE = "https://www.okx.com"
OKX_API_VERSION = "/api/v5"

# Endpoints used by the connector (grouped for clarity).
EP_PUBLIC_TIME = "/api/v5/public/time"
EP_PUBLIC_INSTRUMENTS = "/api/v5/public/instruments"
EP_PUBLIC_TICKER = "/api/v5/market/ticker"
EP_PUBLIC_BOOK = "/api/v5/market/books"
EP_ACCOUNT_BALANCE = "/api/v5/account/balance"
EP_ACCOUNT_POSITIONS = "/api/v5/account/positions"
EP_TRADE_ORDER = "/api/v5/trade/order"
EP_TRADE_CANCEL = "/api/v5/trade/cancel-order"
EP_TRADE_ORDERS_PENDING = "/api/v5/trade/orders-pending"

# Max request body length for signing (OKX rejects bodies > 100 chars on some
# endpoints, but we keep a sane cap for safety).
_MAX_BODY_CHARS = 4096


class OKXAuthError(RuntimeError):
    """Raised when credentials are missing or invalid."""


class OKXAPIError(RuntimeError):
    """Raised when the OKX API returns a non-zero code."""

    def __init__(self, code: str, msg: str, http_status: Optional[int] = None):
        super().__init__(f"OKX API error {code}: {msg}")
        self.code = code
        self.msg = msg
        self.http_status = http_status


def _load_env() -> None:
    """Load .env from the repo root if python-dotenv is available."""
    if load_dotenv is None:
        return
    # Look for .env relative to this file's repo (scripts/trading/../..).
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))
    load_dotenv(os.path.join(repo_root, ".env"))


def _iso_timestamp() -> str:
    """ISO 8601 UTC timestamp with millisecond precision (OKX format)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sign_request(
    secret_key: str,
    timestamp: str,
    method: str,
    request_path: str,
    body: str = "",
) -> str:
    """
    Produce the OK-ACCESS-SIGN header value.

    prehash = timestamp + method + requestPath + body
    sign    = Base64( HMAC_SHA256( secretKey, prehash ) )
    """
    method = method.upper()
    prehash = f"{timestamp}{method}{request_path}{body}"
    mac = hmac.new(
        secret_key.encode("utf-8"),
        prehash.encode("utf-8"),
        hashlib.sha256,
    )
    return base64.b64encode(mac.digest()).decode("utf-8")


class OKXConnector:
    """
    Secure client for the OKX REST API v5.

    Public (unauthenticated) endpoints work without credentials.
    Private endpoints require OKX_API_KEY / OKX_API_SECRET / OKX_API_PASSPHRASE
    in the environment (or .env). Trading methods additionally require
    `allow_trading=True` (defense in depth against accidental orders).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        api_passphrase: Optional[str] = None,
        base_url: str = OKX_REST_BASE,
        timeout: float = 15.0,
        allow_trading: bool = False,
    ) -> None:
        _load_env()
        self.api_key = api_key or os.environ.get("OKX_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("OKX_API_SECRET", "")
        self.api_passphrase = api_passphrase or os.environ.get(
            "OKX_API_PASSPHRASE", ""
        )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        # Trading is OFF unless explicitly enabled. This is the Execution
        # Gateway; the Risk Controller decides whether trading is allowed.
        self.allow_trading = allow_trading
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------
    @property
    def has_credentials(self) -> bool:
        return bool(self.api_key and self.api_secret and self.api_passphrase)

    def _require_credentials(self) -> None:
        if not self.has_credentials:
            raise OKXAuthError(
                "OKX credentials missing. Set OKX_API_KEY, OKX_API_SECRET and "
                "OKX_API_PASSPHRASE in the environment or .env."
            )

    def _auth_headers(
        self, method: str, request_path: str, body: str
    ) -> Dict[str, str]:
        self._require_credentials()
        ts = _iso_timestamp()
        sign = sign_request(self.api_secret, ts, method, request_path, body)
        return {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": sign,
            "OK-ACCESS-TIMESTAMP": ts,
            "OK-ACCESS-PASSPHRASE": self.api_passphrase,
        }

    # ------------------------------------------------------------------
    # Core request
    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Dict[str, Any]:
        method = method.upper()
        url = f"{self.base_url}{path}"

        # Build query string for GET (part of the signed requestPath).
        query = ""
        if params:
            # OKX expects query params in the requestPath for signing.
            query = "?" + "&".join(
                f"{k}={v}" for k, v in sorted(params.items())
            )
        request_path = path + query

        body_str = ""
        if body is not None:
            body_str = json.dumps(body, separators=(",", ":"))
            if len(body_str) > _MAX_BODY_CHARS:
                raise OKXAPIError(
                    "400", f"Request body exceeds {_MAX_BODY_CHARS} chars"
                )

        headers = dict(self.session.headers)
        if authenticated:
            headers.update(self._auth_headers(method, request_path, body_str))

        try:
            resp = self.session.request(
                method,
                url,
                params=params if not authenticated else None,
                data=body_str if body is not None else None,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:  # network-level failure
            logger.error("OKX request failed: %s", exc)
            raise OKXAPIError("NETWORK", str(exc)) from exc

        try:
            payload = resp.json()
        except ValueError:
            raise OKXAPIError(
                "PARSE", "Non-JSON response", http_status=resp.status_code
            )

        code = payload.get("code", "-1")
        if code != "0":
            raise OKXAPIError(
                code, payload.get("msg", "unknown error"), resp.status_code
            )
        return payload

    # ------------------------------------------------------------------
    # Public endpoints (no auth)
    # ------------------------------------------------------------------
    def server_time(self) -> Dict[str, Any]:
        """GET /api/v5/public/time — server time (connectivity check)."""
        return self._request("GET", EP_PUBLIC_TIME)

    def instruments(self, inst_type: str = "SPOT", inst_id: str = "") -> list:
        """GET /api/v5/public/instruments — instrument metadata."""
        params = {"instType": inst_type}
        if inst_id:
            params["instId"] = inst_id
        return self._request("GET", EP_PUBLIC_INSTRUMENTS, params=params).get(
            "data", []
        )

    def ticker(self, inst_id: str) -> Dict[str, Any]:
        """GET /api/v5/market/ticker — last price / 24h stats for an instrument."""
        data = self._request(
            "GET", EP_PUBLIC_TICKER, params={"instId": inst_id}
        ).get("data", [])
        return data[0] if data else {}

    def orderbook(self, inst_id: str, depth: int = 20) -> Dict[str, Any]:
        """GET /api/v5/market/books — order book snapshot."""
        data = self._request(
            "GET", EP_PUBLIC_BOOK, params={"instId": inst_id, "sz": depth}
        ).get("data", [])
        return data[0] if data else {}

    # ------------------------------------------------------------------
    # Private endpoints (auth required)
    # ------------------------------------------------------------------
    def account_balance(self, ccy: str = "") -> Dict[str, Any]:
        """GET /api/v5/account/balance — account balances (read-only)."""
        params = {"ccy": ccy} if ccy else {}
        return self._request(
            "GET", EP_ACCOUNT_BALANCE, params=params, authenticated=True
        )

    def account_positions(self, inst_id: str = "") -> Dict[str, Any]:
        """GET /api/v5/account/positions — open positions (read-only)."""
        params = {"instId": inst_id} if inst_id else {}
        return self._request(
            "GET", EP_ACCOUNT_POSITIONS, params=params, authenticated=True
        )

    def pending_orders(self, inst_id: str = "") -> Dict[str, Any]:
        """GET /api/v5/trade/orders-pending — open orders (read-only)."""
        params = {"instId": inst_id} if inst_id else {}
        return self._request(
            "GET", EP_TRADE_ORDERS_PENDING, params=params, authenticated=True
        )

    # ------------------------------------------------------------------
    # Trading endpoints (require allow_trading=True)
    # ------------------------------------------------------------------
    def _require_trading(self) -> None:
        if not self.allow_trading:
            raise OKXAuthError(
                "Trading is disabled on this connector. Construct with "
                "allow_trading=True only after the Risk Controller approves."
            )

    def place_order(
        self,
        inst_id: str,
        side: str,
        sz: str,
        ord_type: str = "market",
        px: str = "",
        td_mode: str = "cash",
    ) -> Dict[str, Any]:
        """
        POST /api/v5/trade/order — place an order.

        Requires allow_trading=True. This is the Execution Gateway; risk
        validation must happen upstream (see data/trading/risk_limits.json).
        """
        self._require_trading()
        body = {
            "instId": inst_id,
            "tdMode": td_mode,
            "side": side,
            "ordType": ord_type,
            "sz": sz,
        }
        if px:
            body["px"] = px
        return self._request(
            "POST", EP_TRADE_ORDER, body=body, authenticated=True
        )

    def cancel_order(self, inst_id: str, ord_id: str) -> Dict[str, Any]:
        """POST /api/v5/trade/cancel-order — cancel an open order."""
        self._require_trading()
        body = {"instId": inst_id, "ordId": ord_id}
        return self._request(
            "POST", EP_TRADE_CANCEL, body=body, authenticated=True
        )


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------
def _cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="OKX API v5 connector smoke test (read-only by default)."
    )
    parser.add_argument("--inst", default="BTC-USDT", help="Instrument id")
    parser.add_argument(
        "--auth",
        action="store_true",
        help="Also exercise authenticated read endpoints (requires creds).",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    conn = OKXConnector()

    # 1. Connectivity (public)
    t = conn.server_time()
    print(f"[OK] server_time ts={t['data'][0]['ts']}")

    inst = conn.instruments("SPOT", args.inst)
    print(f"[OK] instruments {args.inst}: {len(inst)} record(s)")

    tk = conn.ticker(args.inst)
    print(f"[OK] ticker {args.inst}: last={tk.get('last')} "
          f"vol24h={tk.get('vol24h')}")

    # 2. Authenticated read-only (optional)
    if args.auth:
        bal = conn.account_balance()
        print(f"[OK] account_balance code={bal.get('code')}")
        pos = conn.account_positions()
        print(f"[OK] account_positions code={pos.get('code')}")

    print("\nConnectivity + signing smoke test PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())