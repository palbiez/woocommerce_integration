from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import (
    add_common_args,
    load_config,
    load_woocommerce_config,
    main_guard,
    output_dir,
    read_json,
    timestamp,
    wc_get,
    wc_post,
    wc_put,
    write_json,
)


def clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = {}
    for key, value in payload.items():
        if value is None:
            continue
        if value == "":
            continue
        cleaned[key] = value
    return cleaned


def validate_preview(preview: dict[str, Any], allow_missing_sku: bool) -> None:
    missing = [item["listing_id"] for item in preview.get("items") or [] if item.get("has_missing_sku")]
    if missing and not allow_missing_sku:
        raise RuntimeError(
            "Preview enthaelt fehlende SKUs. Erst korrigieren oder bewusst --allow-missing-sku setzen. "
            f"Listings: {', '.join(map(str, missing[:20]))}"
        )


def existing_product_by_listing_id(wc: Any, listing_id: Any) -> dict[str, Any] | None:
    """Find an earlier import by its private Etsy listing metadata."""
    page = 1
    while True:
        products = wc_get(wc, "products", {"per_page": 100, "page": page})
        if not products:
            return None
        for product in products:
            for meta in product.get("meta_data") or []:
                if meta.get("key") == "_etsy_listing_id" and str(meta.get("value")) == str(listing_id):
                    return product
        if len(products) < 100:
            return None
        page += 1


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1-090: Import-Preview kontrolliert nach WooCommerce schreiben. Ohne --apply nur Dry-Run."
    )
    add_common_args(parser)
    parser.add_argument(
        "--preview",
        default=str(output_dir("m1_import_preview") / "latest.json"),
        help="Pfad zur Import-Preview JSON.",
    )
    parser.add_argument("--apply", action="store_true", help="Erst mit diesem Flag wird nach WooCommerce geschrieben.")
    parser.add_argument("--limit", type=int, default=0, help="Optional nur die ersten N Produkte verarbeiten.")
    parser.add_argument("--allow-missing-sku", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    wc = load_woocommerce_config(config)
    preview = read_json(Path(args.preview))
    validate_preview(preview, args.allow_missing_sku)

    items = preview.get("items") or []
    if args.limit:
        items = items[: args.limit]

    results: list[dict[str, Any]] = []
    for item in items:
        product_payload = clean_payload(item["product"])
        result = {
            "listing_id": item["listing_id"],
            "source_title": item["source_title"],
            "dry_run": not args.apply,
            "product_payload": product_payload,
            "woocommerce_product_id": None,
            "variations": [],
        }

        if args.apply:
            existing = existing_product_by_listing_id(wc, item["listing_id"])
            if existing:
                created = wc_put(wc, f"products/{existing['id']}", product_payload)
                result["action"] = "updated"
            else:
                created = wc_post(wc, "products", product_payload)
                result["action"] = "created"
            product_id = created["id"]
            result["woocommerce_product_id"] = product_id
            existing_variations = {}
            if existing and created.get("type") == "variable":
                current = wc_get(wc, f"products/{product_id}/variations", {"per_page": 100, "page": 1})
                existing_variations = {str(v.get("sku")): v for v in current or [] if v.get("sku")}
            for variation in item.get("variations") or []:
                sku = str(variation.get("sku") or "")
                if sku in existing_variations:
                    variation_id = existing_variations[sku]["id"]
                    created_variation = wc_put(
                        wc, f"products/{product_id}/variations/{variation_id}", clean_payload(variation)
                    )
                    action = "updated"
                else:
                    created_variation = wc_post(
                        wc, f"products/{product_id}/variations", clean_payload(variation)
                    )
                    action = "created"
                result["variations"].append(
                    {
                        "sku": variation.get("sku"),
                        "woocommerce_variation_id": created_variation.get("id"),
                        "action": action,
                    }
                )
        else:
            result["action"] = "dry-run"
            result["variations"] = [
                {"sku": variation.get("sku"), "woocommerce_variation_id": None}
                for variation in item.get("variations") or []
            ]

        results.append(result)

    out_dir = output_dir("m1_import_results")
    out = out_dir / f"woocommerce-import-{'apply' if args.apply else 'dry-run'}-{timestamp()}.json"
    write_json(
        out,
        {
            "preview": str(Path(args.preview)),
            "applied": args.apply,
            "count": len(results),
            "results": results,
        },
    )
    print(f"Import-Ergebnis geschrieben: {out}")
    if not args.apply:
        print("Dry-Run: Es wurde nichts nach WooCommerce geschrieben. Fuer echten Import --apply setzen.")


if __name__ == "__main__":
    main_guard(run)
