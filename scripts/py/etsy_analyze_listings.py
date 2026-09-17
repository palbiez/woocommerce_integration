from __future__ import annotations

import argparse
import re
from collections import Counter
from typing import Any

from common import (
    add_common_args,
    etsy_get,
    load_config,
    load_etsy_config,
    load_etsy_token,
    main_guard,
    output_dir,
    refresh_etsy_token_if_needed,
    resolve_etsy_shop_id,
    ScriptError,
    timestamp,
    write_csv,
    write_json,
)


BUNDLE_HINTS = re.compile(r"\b(bundle|set|kit|paket|bundle|starter)\b", re.IGNORECASE)


def iter_active_listings(etsy: Any, token: dict[str, Any], shop_id: str, limit: int) -> list[dict[str, Any]]:
    listings: list[dict[str, Any]] = []
    offset = 0
    page_size = 100 if limit <= 0 else min(limit, 100)

    while True:
        payload = etsy_get(
            etsy,
            f"application/shops/{shop_id}/listings",
            token=token,
            params={"state": "active", "limit": page_size, "offset": offset},
        )
        page = payload.get("results", payload if isinstance(payload, list) else [])
        listings.extend(page)
        if len(page) < page_size:
            break
        if limit and len(listings) >= limit:
            listings = listings[:limit]
            break
        offset += page_size
    return listings


def extract_inventory_skus(inventory: dict[str, Any]) -> list[str]:
    skus: list[str] = []
    for product in inventory.get("products") or []:
        sku = str(product.get("sku") or "").strip()
        if sku:
            skus.append(sku)
    return skus


def listing_special_cases(listing: dict[str, Any], inventory: dict[str, Any], skus: list[str]) -> list[str]:
    cases: list[str] = []
    title = str(listing.get("title") or "")
    products = inventory.get("products") or []

    if not skus or len(skus) < len(products):
        cases.append("missing_sku")
    if len(products) > 1:
        cases.append("variants")
    if listing.get("is_personalizable") or listing.get("personalization_is_required"):
        cases.append("personalized")
    if listing.get("processing_min") or listing.get("processing_max"):
        cases.append("made_to_order_candidate")
    if BUNDLE_HINTS.search(title):
        cases.append("bundle_candidate")
    return cases


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1-030: Etsy Listings, Varianten, Preise, Bilder und Sonderfaelle analysieren."
    )
    add_common_args(parser)
    parser.add_argument("--limit", type=int, default=100, help="Maximale Anzahl Listings.")
    args = parser.parse_args()

    config = load_config(args.config)
    etsy = load_etsy_config(config)
    token = refresh_etsy_token_if_needed(etsy, load_etsy_token())
    shop_id = resolve_etsy_shop_id(etsy, token)

    listings = iter_active_listings(etsy, token, shop_id, args.limit)
    rows: list[dict[str, Any]] = []
    full: list[dict[str, Any]] = []
    all_skus: list[str] = []

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
        skus = extract_inventory_skus(inventory)
        all_skus.extend(skus)
        cases = listing_special_cases(listing, inventory, skus)
        image_results = images.get("results", images if isinstance(images, list) else [])

        row = {
            "listing_id": listing_id,
            "title": listing.get("title"),
            "state": listing.get("state"),
            "url": listing.get("url"),
            "price": listing.get("price", {}).get("amount")
            if isinstance(listing.get("price"), dict)
            else listing.get("price"),
            "currency": listing.get("price", {}).get("currency_code")
            if isinstance(listing.get("price"), dict)
            else listing.get("currency_code"),
            "sku_count": len(skus),
            "skus": "|".join(skus),
            "image_count": len(image_results),
            "personalizable": bool(listing.get("is_personalizable")),
            "personalization_required": bool(listing.get("personalization_is_required")),
            "special_cases": "|".join(cases),
        }
        rows.append(row)
        full.append({"listing": listing, "inventory": inventory, "images": image_results, "analysis": row})

    sku_counts = Counter(all_skus)
    duplicates = sorted(sku for sku, count in sku_counts.items() if count > 1)
    summary = {
        "shop_id": shop_id,
        "listing_count": len(listings),
        "sku_count": len(all_skus),
        "duplicate_skus": duplicates,
        "missing_sku_listings": [row["listing_id"] for row in rows if "missing_sku" in row["special_cases"]],
        "special_case_counts": dict(
            Counter(case for row in rows for case in str(row["special_cases"]).split("|") if case)
        ),
    }

    out_dir = output_dir("m1_etsy_analysis")
    stamp = timestamp()
    write_json(out_dir / f"etsy-analysis-{stamp}.json", {"summary": summary, "items": full})
    write_csv(
        out_dir / f"etsy-analysis-{stamp}.csv",
        rows,
        [
            "listing_id",
            "title",
            "state",
            "url",
            "price",
            "currency",
            "sku_count",
            "skus",
            "image_count",
            "personalizable",
            "personalization_required",
            "special_cases",
        ],
    )
    write_json(out_dir / "latest.json", {"summary": summary, "items": full})
    print(f"Etsy Analyse geschrieben: {out_dir}")
    print(f"Listings: {summary['listing_count']}, SKUs: {summary['sku_count']}")
    if duplicates:
        print(f"Doppelte SKUs: {', '.join(duplicates)}")
    if summary["missing_sku_listings"]:
        print(f"Listings mit fehlender SKU: {len(summary['missing_sku_listings'])}")


if __name__ == "__main__":
    main_guard(run)
