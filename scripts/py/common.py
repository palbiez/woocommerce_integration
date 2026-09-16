from __future__ import annotations

import argparse
import configparser
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config.cfg"
SECRET_DIR = PROJECT_ROOT / ".secrets"
DATA_DIR = PROJECT_ROOT / "data"
ETSY_TOKEN_FILE = SECRET_DIR / "etsy_token.json"
USER_AGENT = "woocommerce-etsy-integration/0.1"


class ScriptError(RuntimeError):
    pass


@dataclass(frozen=True)
class WooConfig:
    base_url: str
    api_key: str
    api_secret: str
    config_path: str


@dataclass(frozen=True)
class EtsyConfig:
    keystring: str
    secret: str
    shop_id: str | None


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Pfad zur config.cfg. Standard: Projektverzeichnis/config.cfg",
    )


def load_config(path: str | Path) -> configparser.ConfigParser:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ScriptError(f"Config-Datei nicht gefunden: {cfg_path}")

    config = configparser.ConfigParser()
    read_files = config.read(cfg_path, encoding="utf-8")
    if not read_files:
        raise ScriptError(f"Config-Datei konnte nicht gelesen werden: {cfg_path}")
    config["_meta"] = {"path": str(cfg_path.resolve())}
    return config


def normalize_url(value: str, section: str, key: str) -> str:
    normalized = value.strip().strip('"').strip("'").rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ScriptError(
            f"Ungueltige URL in {section}.{key}: {value!r}. Erwartet wird z. B. https://shop.mrs-daui.de"
        )
    return normalized


def require_value(config: configparser.ConfigParser, section: str, key: str) -> str:
    if not config.has_section(section):
        raise ScriptError(f"Section fehlt in config.cfg: [{section}]")
    value = config.get(section, key, fallback="").strip()
    if not value:
        raise ScriptError(f"Config-Wert fehlt: {section}.{key}")
    return value


def load_woocommerce_config(config: configparser.ConfigParser) -> WooConfig:
    url = require_value(config, "Woocommerce", "Url")
    return WooConfig(
        base_url=normalize_url(url, "Woocommerce", "Url"),
        api_key=require_value(config, "Woocommerce", "ApiKey"),
        api_secret=require_value(config, "Woocommerce", "ApiSecret"),
        config_path=config.get("_meta", "path", fallback=str(DEFAULT_CONFIG)),
    )


def load_etsy_config(config: configparser.ConfigParser) -> EtsyConfig:
    shop_id = config.get("EtsyAPI", "ShopId", fallback="").strip() or None
    return EtsyConfig(
        keystring=require_value(config, "EtsyAPI", "KeyString"),
        secret=config.get("EtsyAPI", "Secret", fallback="").strip(),
        shop_id=shop_id,
    )


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_writable_dir(path: Path) -> Path:
    ensure_dir(path)
    test_file = path / ".write-test"
    try:
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
    except OSError as exc:
        raise ScriptError(f"Verzeichnis ist nicht beschreibbar: {path} ({exc})") from exc
    return path


def timestamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def output_dir(name: str) -> Path:
    return ensure_dir(DATA_DIR / name)


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fail(message: str) -> None:
    print(f"Fehler: {message}", file=sys.stderr)
    raise SystemExit(1)


def request_json(
    method: str,
    url: str,
    *,
    timeout: int = 30,
    expected: tuple[int, ...] = (200,),
    **kwargs: Any,
) -> Any:
    headers = kwargs.pop("headers", {}) or {}
    headers.setdefault("User-Agent", USER_AGENT)

    response = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
    if response.status_code not in expected:
        body = response.text[:2000]
        raise ScriptError(f"HTTP {response.status_code} fuer {url}: {body}")
    if not response.content:
        return None
    return response.json()


def wc_url(wc: WooConfig, endpoint: str) -> str:
    return urljoin(f"{wc.base_url}/", f"wp-json/wc/v3/{endpoint.lstrip('/')}")


def wc_get(wc: WooConfig, endpoint: str, params: dict[str, Any] | None = None) -> Any:
    return request_json(
        "GET",
        wc_url(wc, endpoint),
        params=params or {},
        auth=(wc.api_key, wc.api_secret),
    )


def wc_post(wc: WooConfig, endpoint: str, payload: dict[str, Any]) -> Any:
    return request_json(
        "POST",
        wc_url(wc, endpoint),
        json=payload,
        auth=(wc.api_key, wc.api_secret),
        expected=(200, 201),
    )


def wc_put(wc: WooConfig, endpoint: str, payload: dict[str, Any]) -> Any:
    return request_json(
        "PUT",
        wc_url(wc, endpoint),
        json=payload,
        auth=(wc.api_key, wc.api_secret),
        expected=(200, 201),
    )


def etsy_api_key_header(etsy: EtsyConfig) -> str:
    override = os.environ.get("ETSY_API_KEY_HEADER", "").strip()
    if override:
        return override
    if etsy.secret:
        return f"{etsy.keystring}:{etsy.secret}"
    return etsy.keystring


def load_etsy_token(token_file: Path = ETSY_TOKEN_FILE) -> dict[str, Any]:
    if not token_file.exists():
        raise ScriptError(
            f"Etsy Token fehlt: {token_file}. Erst scripts/py/etsy_oauth.py ausfuehren."
        )
    return read_json(token_file)


def save_etsy_token(token: dict[str, Any], token_file: Path = ETSY_TOKEN_FILE) -> None:
    now = int(time.time())
    token = dict(token)
    token.setdefault("created_at", now)
    if "expires_in" in token:
        token["expires_at"] = now + int(token["expires_in"])
    write_json(token_file, token)
    try:
        os.chmod(token_file, 0o600)
    except OSError:
        pass


def refresh_etsy_token_if_needed(
    etsy: EtsyConfig,
    token: dict[str, Any],
    *,
    force: bool = False,
) -> dict[str, Any]:
    expires_at = int(token.get("expires_at", 0) or 0)
    if not force and expires_at and expires_at - int(time.time()) > 300:
        return token

    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise ScriptError("Etsy refresh_token fehlt; OAuth Flow erneut ausfuehren.")

    refreshed = request_json(
        "POST",
        "https://api.etsy.com/v3/public/oauth/token",
        expected=(200,),
        data={
            "grant_type": "refresh_token",
            "client_id": etsy.keystring,
            "refresh_token": refresh_token,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "x-api-key": etsy_api_key_header(etsy),
        },
    )
    save_etsy_token(refreshed)
    return refreshed


def etsy_headers(etsy: EtsyConfig, token: dict[str, Any] | None = None) -> dict[str, str]:
    headers = {
        "x-api-key": etsy_api_key_header(etsy),
        "Accept": "application/json",
    }
    if token and token.get("access_token"):
        headers["Authorization"] = f"Bearer {token['access_token']}"
    return headers


def etsy_get(
    etsy: EtsyConfig,
    endpoint: str,
    *,
    token: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    url = urljoin("https://api.etsy.com/v3/", endpoint.lstrip("/"))
    return request_json("GET", url, headers=etsy_headers(etsy, token), params=params or {})


def resolve_etsy_shop_id(etsy: EtsyConfig, token: dict[str, Any]) -> str:
    if etsy.shop_id:
        return etsy.shop_id

    me = etsy_get(etsy, "application/users/me", token=token)
    for key in ("shop_id", "primary_shop_id"):
        value = me.get(key) if isinstance(me, dict) else None
        if value:
            return str(value)

    raise ScriptError(
        "ShopId konnte nicht automatisch ermittelt werden. Bitte EtsyAPI.ShopId in config.cfg setzen."
    )


def main_guard(func: Any) -> None:
    try:
        func()
    except ScriptError as exc:
        fail(str(exc))
    except requests.RequestException as exc:
        fail(f"HTTP/Netzwerkfehler: {exc}")
    except RuntimeError as exc:
        fail(str(exc))
    except TimeoutError as exc:
        fail(str(exc))
