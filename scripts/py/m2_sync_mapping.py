from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_CONFIG,
    DATA_DIR,
    add_common_args,
    load_config,
    load_woocommerce_config,
    main_guard,
    read_json,
    wc_get,
    write_json,
)
from m2_mapping_db import connect, init_db, validate_sku


DEFAULT_ANALYSIS = DATA_DIR / "m1_etsy_analysis" / "latest.json"
DEFAULT_DB = DATA_DIR / "m2_mapping" / "mapping.sqlite3"


def meta_value(product: dict[str, Any], key: str) -> str | None:
    for entry in product.get("meta_data") or []:
        if entry.get("key") == key:
            value = entry.get("value")
            return str(value) if value is not None else None
    return None


def load_woo_products(config: Any) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    wc = load_woocommerce_config(config)
    products = wc_get(wc, "products", {"per_page": 100, "page": 1})
    by_listing: dict[str, dict[str, Any]] = {}
    by_sku: dict[str, dict[str, Any]] = {}
    for product in products:
        listing_id = meta_value(product, "_etsy_listing_id")
        if listing_id:
            by_listing[listing_id] = product
        if product.get("sku"):
            by_sku[str(product["sku"]).strip().lower()] = {
                "product": product,
                "variation": None,
            }
        if product.get("type") == "variable":
            variations = wc_get(wc, f"products/{product['id']}/variations", {"per_page": 100, "page": 1})
            for variation in variations or []:
                if variation.get("sku"):
                    by_sku[str(variation["sku"]).strip().lower()] = {
                        "product": product,
                        "variation": variation,
                    }
    return by_listing, by_sku


def upsert_mapping(conn: Any, values: dict[str, Any]) -> str:
    sku = validate_sku(values["sku"])
    values["sku"] = sku
    row = conn.execute(
        "SELECT id FROM product_mapping WHERE lower(sku) = lower(?)",
        (sku,),
    ).fetchone()
    columns = [
        "sku", "product_kind", "woocommerce_product_id", "woocommerce_variation_id",
        "etsy_listing_id", "etsy_product_id", "etsy_offering_id", "sync_status",
        "review_reason", "last_seen_source",
    ]
    params = tuple(values.get(column) for column in columns)
    if row:
        assignments = ", ".join(f"{column} = ?" for column in columns[1:])
        conn.execute(
            f"UPDATE product_mapping SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params[1:] + (row["id"],),
        )
        event = "linked" if values["sync_status"] == "linked" else "updated"
        message = f"Mapping fuer SKU {sku} synchronisiert."
    else:
        cursor = conn.execute(
            f"INSERT INTO product_mapping ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            params,
        )
        row = {"id": cursor.lastrowid}
        event = "linked" if values["sync_status"] == "linked" else "needs_review"
        message = f"Mapping fuer SKU {sku} angelegt."
    conn.execute(
        "INSERT INTO mapping_event (mapping_id, event_type, source, message, payload_json) VALUES (?, ?, 'sync', ?, ?)",
        (row["id"], event, message, json.dumps(values, ensure_ascii=False)),
    )
    return event


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M2-010: Etsy-SKUs mit WooCommerce-Produkten/Varianten persistent verknuepfen."
    )
    add_common_args(parser)
    parser.add_argument("--analysis", default=str(DEFAULT_ANALYSIS))
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args()

    config = load_config(args.config or str(DEFAULT_CONFIG))
    analysis = read_json(Path(args.analysis))
    db_path = Path(args.db)
    init_db(db_path)
    by_listing, by_sku = load_woo_products(config)
    counts = {"linked": 0, "needs_review": 0, "updated": 0}
    with connect(db_path) as conn:
        for item in analysis.get("items") or []:
            listing = item["listing"]
            listing_id = str(listing["listing_id"])
            woo_product = by_listing.get(listing_id)
            for etsy_product in item.get("inventory", {}).get("products") or []:
                sku = str(etsy_product.get("sku") or "").strip()
                if not sku:
                    continue
                woo_match = by_sku.get(sku.lower())
                if woo_match:
                    woo_parent = woo_match["product"]
                    woo_variation = woo_match["variation"]
                    kind = "variation" if woo_variation else "simple"
                    woo_product_id = woo_parent.get("id")
                    woo_variation_id = woo_variation.get("id") if woo_variation else None
                    status = "linked"
                    reason = None
                else:
                    kind = "variation" if len(item.get("inventory", {}).get("products") or []) > 1 else "simple"
                    woo_product_id = woo_product.get("id") if woo_product else None
                    woo_variation_id = None
                    status = "needs_review"
                    reason = "SKU in Etsy vorhanden, aber keine passende WooCommerce-SKU gefunden."
                values = {
                    "sku": sku,
                    "product_kind": kind,
                    "woocommerce_product_id": woo_product_id,
                    "woocommerce_variation_id": woo_variation_id,
                    "etsy_listing_id": int(listing_id),
                    "etsy_product_id": etsy_product.get("product_id"),
                    "etsy_offering_id": (etsy_product.get("offerings") or [{}])[0].get("offering_id"),
                    "sync_status": status,
                    "review_reason": reason,
                    "last_seen_source": "sync",
                }
                event = upsert_mapping(conn, values)
                counts[event] = counts.get(event, 0) + 1
    report = {"analysis": str(Path(args.analysis)), "db": str(db_path), "counts": counts}
    out = DATA_DIR / "m2_mapping" / "latest-sync.json"
    write_json(out, report)
    print(f"Mapping synchronisiert: {sum(counts.values())}")
    print(json.dumps(counts, ensure_ascii=False, sort_keys=True))
    print(f"Report: {out}")


if __name__ == "__main__":
    main_guard(run)
