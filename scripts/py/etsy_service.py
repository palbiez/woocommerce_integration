from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import html
import json
import os
import secrets
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from common import (
    ETSY_TOKEN_FILE,
    DATA_DIR,
    etsy_api_key_header,
    etsy_get,
    load_config,
    load_etsy_config,
    load_etsy_token,
    request_json,
    save_etsy_token,
    write_json,
    ScriptError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PENDING_FILE = PROJECT_ROOT / ".secrets" / "etsy_oauth_pending.json"
WOOCOMMERCE_WEBHOOK_SECRET_FILE = PROJECT_ROOT / ".secrets" / "woocommerce_webhook_secret"
SNAPSHOT_FILE = DATA_DIR / "m1_etsy_snapshot" / "latest.json"
WEBHOOK_DIR = DATA_DIR / "etsy_webhooks"
WOOCOMMERCE_WEBHOOK_DIR = DATA_DIR / "woocommerce_webhooks"
DEFAULT_SCOPES = ["listings_r", "listings_w", "shops_r", "profile_r", "transactions_r"]
WEBHOOK_MAX_AGE_SECONDS = 300


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def redirect_uri(config: Any) -> str:
    app = config["AppData_server"]
    explicit = app.get("OAuthRedirectUri", "").strip()
    if explicit:
        return explicit
    domain = app.get("Domain", "").strip()
    port = app.get("ExternalPort", "8443").strip()
    suffix = f":{port}" if port and port != "443" else ""
    return f"https://{domain}{suffix}/oauth/etsy/callback"


def save_pending(state: str, verifier: str, callback: str) -> None:
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        PENDING_FILE,
        {"state": state, "verifier": verifier, "redirect_uri": callback, "created_at": int(time.time())},
    )
    PENDING_FILE.chmod(0o600)


def load_pending() -> dict[str, Any]:
    if not PENDING_FILE.exists():
        raise RuntimeError("Kein aktiver Etsy-OAuth-Vorgang gefunden.")
    pending = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    if int(time.time()) - int(pending.get("created_at", 0)) > 600:
        PENDING_FILE.unlink(missing_ok=True)
        raise RuntimeError("Etsy-OAuth-Vorgang ist abgelaufen; bitte neu starten.")
    return pending


def discover_shop_id(etsy: Any, token: dict[str, Any]) -> str:
    if etsy.shop_id:
        return etsy.shop_id
    access_token = str(token.get("access_token") or "")
    user_id = access_token.split(".", 1)[0]
    if not user_id.isdigit():
        me = etsy_get(etsy, "application/users/me", token=token)
        user_id = str(me.get("user_id") or "")
    if not user_id.isdigit():
        raise RuntimeError("Shop-ID konnte aus dem Etsy-OAuth-Token nicht ermittelt werden.")
    shops = etsy_get(etsy, f"application/users/{user_id}/shops", token=token)
    if isinstance(shops, dict) and shops.get("shop_id"):
        results = [shops]
    else:
        results = shops.get("results", shops if isinstance(shops, list) else [])
    if not results or not results[0].get("shop_id"):
        raise RuntimeError("Für den Etsy-Seller wurde kein Shop gefunden.")
    return str(results[0]["shop_id"])


def collect_snapshot(config: Any) -> dict[str, Any]:
    etsy = load_etsy_config(config)
    token = load_etsy_token()
    shop_id = discover_shop_id(etsy, token)
    listings: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = etsy_get(
            etsy,
            f"application/shops/{shop_id}/listings",
            token=token,
            params={"state": "active", "limit": 100, "offset": offset},
        )
        results = page.get("results", page if isinstance(page, list) else [])
        listings.extend(results)
        if len(results) < 100:
            break
        offset += 100

    items: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for listing in listings:
        listing_id = listing["listing_id"]
        inventory = etsy_get(etsy, f"application/listings/{listing_id}/inventory", token=token)
        try:
            images = etsy_get(
                etsy,
                f"application/listings/{listing_id}/images",
                token=token,
            )
        except ScriptError as exc:
            if "HTTP 404" not in str(exc):
                raise
            images = {"results": []}
            warnings.append({"listing_id": listing_id, "type": "images_not_found"})
        items.append(
            {
                "listing": listing,
                "inventory": inventory,
                "images": images.get("results", images if isinstance(images, list) else []),
            }
        )

    snapshot = {
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "shop_id": shop_id,
        "listing_count": len(items),
        "warnings": warnings,
        "items": items,
    }
    write_json(SNAPSHOT_FILE, snapshot)
    return snapshot


class EtsyService(BaseHTTPRequestHandler):
    server: "ServiceServer"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/oauth/etsy/callback":
            handle_oauth_callback(self, parsed)
            return
        if parsed.path == "/healthz":
            self._send_json(200, {"status": "ok", "service": "woocommerce-etsy", "port": self.server.server_port})
            return
        if parsed.path == "/oauth/etsy/start":
            verifier = secrets.token_urlsafe(64)
            state = secrets.token_urlsafe(24)
            callback = redirect_uri(self.server.config)
            save_pending(state, verifier, callback)
            params = {
                "response_type": "code",
                "redirect_uri": callback,
                "scope": " ".join(DEFAULT_SCOPES),
                "client_id": self.server.etsy.keystring,
                "state": state,
                "code_challenge": code_challenge(verifier),
                "code_challenge_method": "S256",
            }
            target = "https://www.etsy.com/oauth/connect?" + urllib.parse.urlencode(params)
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()
            return
        if parsed.path == "/api/etsy/snapshot":
            if not SNAPSHOT_FILE.exists():
                self._send_json(404, {"error": "Noch kein Etsy-Snapshot vorhanden."})
                return
            self._send_json(200, json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8")))
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/webhooks/woocommerce":
            handle_woocommerce_webhook(self)
            return
        if self.path != "/webhooks/etsy":
            self._send_json(404, {"error": "not_found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1024 * 1024:
            self._send_json(413, {"error": "payload_too_large"})
            return
        raw = self.rfile.read(length)
        webhook_id = self.headers.get("webhook-id", "").strip()
        webhook_timestamp = self.headers.get("webhook-timestamp", "").strip()
        webhook_signature = self.headers.get("webhook-signature", "").strip()
        secret = self.server.config.get("EtsyAPI", "WebhookSecret", fallback="").strip()
        if not secret:
            self._send_json(503, {"error": "webhook_secret_not_configured"})
            return
        try:
            timestamp_value = int(webhook_timestamp)
            if abs(int(time.time()) - timestamp_value) > WEBHOOK_MAX_AGE_SECONDS:
                raise ValueError("timestamp_outside_tolerance")
            encoded_secret = secret.split("_", 1)[1] if secret.startswith("whsec_") else secret
            secret_bytes = base64.b64decode(encoded_secret)
            signed_content = f"{webhook_id}.{webhook_timestamp}.".encode("utf-8") + raw
            expected_signature = base64.b64encode(
                hmac.new(secret_bytes, signed_content, hashlib.sha256).digest()
            ).decode("ascii")
            signatures = [part.split(",", 1)[-1] for part in webhook_signature.split()]
            if not webhook_id or expected_signature not in signatures:
                raise ValueError("invalid_signature")
        except (ValueError, TypeError, binascii.Error):
            self._send_json(401, {"error": "invalid_webhook_signature"})
            return
        safe_id = "".join(ch for ch in webhook_id if ch.isalnum() or ch in "-_")[:100]
        WEBHOOK_DIR.mkdir(parents=True, exist_ok=True)
        target = WEBHOOK_DIR / f"{safe_id}.json"
        if target.exists():
            self._send_json(200, {"accepted": True, "duplicate": True, "webhook_id": webhook_id})
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "invalid_json"})
            return
        write_json(
            target,
            {
                "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "webhook_id": webhook_id,
                "event_type": self.headers.get("webhook-event-type"),
                "payload": payload,
            },
        )
        self._send_json(202, {"accepted": True, "webhook_id": webhook_id})

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Allow", "GET,POST,HEAD,OPTIONS")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        # Never write OAuth codes, state values or webhook query data to logs.
        request_line = str(args[0]) if args else ""
        if request_line.startswith('"') and " " in request_line:
            method, target, *_ = request_line.strip('"').split(" ", 2)
            request_line = f'"{method} {urllib.parse.urlsplit(target).path} HTTP"'
        print(f"{self.address_string()} - {request_line}", flush=True)


def handle_oauth_callback(self: EtsyService, parsed: Any) -> None:
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("error"):
        self._send_json(400, {"error": query["error"][0]})
        return
    try:
        pending = load_pending()
        state = (query.get("state") or [""])[0]
        code = (query.get("code") or [""])[0]
        if not code or state != pending.get("state"):
            raise RuntimeError("OAuth-Code fehlt oder State stimmt nicht überein.")
        token = request_json(
            "POST",
            "https://api.etsy.com/v3/public/oauth/token",
            expected=(200,),
            data={
                "grant_type": "authorization_code",
                "client_id": self.server.etsy.keystring,
                "redirect_uri": pending["redirect_uri"],
                "code": code,
                "code_verifier": pending["verifier"],
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "x-api-key": etsy_api_key_header(self.server.etsy),
            },
        )
        save_etsy_token(token, ETSY_TOKEN_FILE)
        PENDING_FILE.unlink(missing_ok=True)
        snapshot = collect_snapshot(self.server.config)
        body = (
            "<html><body><h1>Etsy Verbindung erfolgreich</h1>"
            f"<p>{html.escape(str(snapshot['listing_count']))} Listings gespeichert.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    except Exception as exc:  # callback must return a safe diagnostic, never credentials
        self._send_json(500, {"error": str(exc)})


def handle_woocommerce_webhook(self: EtsyService) -> None:
    length = int(self.headers.get("Content-Length", "0"))
    if length > 1024 * 1024:
        self._send_json(413, {"error": "payload_too_large"})
        return
    raw = self.rfile.read(length)
    secret = os.environ.get("WOOCOMMERCE_WEBHOOK_SECRET", "").strip()
    if not secret:
        secret = self.server.config.get("Woocommerce", "WebhookSecret", fallback="").strip()
    if not secret and WOOCOMMERCE_WEBHOOK_SECRET_FILE.exists():
        secret = WOOCOMMERCE_WEBHOOK_SECRET_FILE.read_text(encoding="utf-8").strip()
    if not secret:
        self._send_json(503, {"error": "webhook_secret_not_configured"})
        return
    supplied = self.headers.get("X-WC-Webhook-Signature", "").strip()
    expected = base64.b64encode(hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()).decode("ascii")
    if not supplied or not hmac.compare_digest(supplied, expected):
        self._send_json(401, {"error": "invalid_webhook_signature"})
        return
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        self._send_json(400, {"error": "invalid_json"})
        return
    event_id = self.headers.get("X-WC-Webhook-ID", "").strip()
    if not event_id:
        self._send_json(400, {"error": "missing_webhook_id"})
        return
    safe_id = "".join(ch for ch in event_id if ch.isalnum() or ch in "-_")[:100]
    WOOCOMMERCE_WEBHOOK_DIR.mkdir(parents=True, exist_ok=True)
    target = WOOCOMMERCE_WEBHOOK_DIR / f"{safe_id}.json"
    if target.exists():
        self._send_json(200, {"accepted": True, "duplicate": True, "webhook_id": event_id})
        return
    write_json(
        target,
        {
            "received_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "webhook_id": event_id,
            "topic": self.headers.get("X-WC-Webhook-Topic"),
            "resource": self.headers.get("X-WC-Webhook-Resource"),
            "event": self.headers.get("X-WC-Webhook-Event"),
            "payload": payload,
        },
    )
    self._send_json(202, {"accepted": True, "webhook_id": event_id})
class ServiceServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], config: Any) -> None:
        super().__init__(address, EtsyService)
        self.config = config
        self.etsy = load_etsy_config(config)


def run() -> None:
    parser = argparse.ArgumentParser(description="Kleiner Etsy/WooCommerce OAuth- und Snapshot-Service.")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "config.cfg"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6001)
    args = parser.parse_args()
    config = load_config(args.config)
    server = ServiceServer((args.host, args.port), config)
    print(f"Etsy service listening on {args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
