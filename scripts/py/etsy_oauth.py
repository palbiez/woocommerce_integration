from __future__ import annotations

import argparse
import base64
import hashlib
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from common import (
    ETSY_TOKEN_FILE,
    add_common_args,
    etsy_api_key_header,
    load_config,
    load_etsy_config,
    main_guard,
    request_json,
    save_etsy_token,
)


DEFAULT_SCOPES = [
    "listings_r",
    "listings_w",
    "shops_r",
    "profile_r",
    "transactions_r",
]


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


class OAuthCallback(BaseHTTPRequestHandler):
    server: Any

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_result = {
            "code": (params.get("code") or [""])[0],
            "state": (params.get("state") or [""])[0],
            "error": (params.get("error") or [""])[0],
        }
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OAuth Callback erhalten. Dieses Browserfenster kann geschlossen werden.")

    def log_message(self, format: str, *args: Any) -> None:
        return


def wait_for_callback(host: str, port: int) -> dict[str, str]:
    server = HTTPServer((host, port), OAuthCallback)
    server.oauth_result = {}
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=300)
    server.server_close()
    if not server.oauth_result:
        raise TimeoutError("Kein OAuth Callback innerhalb von 300 Sekunden erhalten.")
    return server.oauth_result


def exchange_code(
    *,
    keystring: str,
    api_key_header: str,
    redirect_uri: str,
    code: str,
    verifier: str,
) -> dict[str, Any]:
    return request_json(
        "POST",
        "https://api.etsy.com/v3/public/oauth/token",
        expected=(200,),
        data={
            "grant_type": "authorization_code",
            "client_id": keystring,
            "redirect_uri": redirect_uri,
            "code": code,
            "code_verifier": verifier,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "x-api-key": api_key_header,
        },
    )


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1-020: Etsy OAuth 2.0 PKCE Flow ausfuehren und Token sicher lokal speichern."
    )
    add_common_args(parser)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--redirect-uri", default="")
    parser.add_argument("--scope", nargs="*", default=DEFAULT_SCOPES)
    parser.add_argument("--no-browser", action="store_true", help="Auth-URL nur ausgeben.")
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Keinen lokalen Callback starten; Redirect-URL oder Code manuell einfuegen.",
    )
    parser.add_argument("--code", default="", help="Authorization Code manuell uebergeben.")
    parser.add_argument("--state", default="", help="State manuell setzen, nur mit --code relevant.")
    args = parser.parse_args()

    config = load_config(args.config)
    etsy = load_etsy_config(config)
    redirect_uri = args.redirect_uri or f"http://{args.host}:{args.port}/callback"
    verifier = secrets.token_urlsafe(64)
    state = secrets.token_urlsafe(24)

    auth_params = {
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(args.scope),
        "client_id": etsy.keystring,
        "state": state,
        "code_challenge": code_challenge(verifier),
        "code_challenge_method": "S256",
    }
    auth_url = "https://www.etsy.com/oauth/connect?" + urllib.parse.urlencode(auth_params)

    if args.code:
        code = args.code
        returned_state = args.state or state
    elif args.manual:
        print("Etsy OAuth URL:")
        print(auth_url)
        raw = input("Nach Freigabe komplette Redirect-URL oder nur den code-Parameter einfuegen: ").strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            parsed = urllib.parse.urlparse(raw)
            params = urllib.parse.parse_qs(parsed.query)
            code = (params.get("code") or [""])[0]
            returned_state = (params.get("state") or [""])[0]
        else:
            code = raw
            returned_state = input("state-Parameter einfuegen: ").strip()
    else:
        print("Etsy OAuth URL:")
        print(auth_url)
        if not args.no_browser:
            webbrowser.open(auth_url)
        callback = wait_for_callback(args.host, args.port)
        if callback.get("error"):
            raise RuntimeError(f"Etsy OAuth Fehler: {callback['error']}")
        code = callback.get("code", "")
        returned_state = callback.get("state", "")

    if not code:
        raise RuntimeError("Kein Authorization Code erhalten.")
    if returned_state != state:
        raise RuntimeError("OAuth State stimmt nicht ueberein.")

    token = exchange_code(
        keystring=etsy.keystring,
        api_key_header=etsy_api_key_header(etsy),
        redirect_uri=redirect_uri,
        code=code,
        verifier=verifier,
    )
    save_etsy_token(token, ETSY_TOKEN_FILE)
    print(f"Etsy Token gespeichert: {ETSY_TOKEN_FILE}")


if __name__ == "__main__":
    main_guard(run)
