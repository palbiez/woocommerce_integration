from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import main_guard, output_dir, read_json, timestamp, write_csv, write_json


def money_to_string(value: Any) -> str:
    if isinstance(value, dict):
        amount = value.get("amount")
        divisor = value.get("divisor") or 100
        if amount is not None:
            return f"{float(amount) / float(divisor):.2f}"
    if value is None:
        return ""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def image_src(image: dict[str, Any]) -> str:
    for key in ("url_fullxfull", "url_570xN", "url_300x300", "url_75x75"):
        if image.get(key):
            return image[key]
    return ""


def inventory_products(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return inventory.get("products") or []


def product_sku(product: dict[str, Any], listing_id: Any) -> str:
    sku = str(product.get("sku") or "").strip()
    if sku:
        return sku
    return f"TODO-SKU-{listing_id}"


def has_missing_sku(products: list[dict[str, Any]]) -> bool:
    """Return true when any sellable Etsy inventory product has no SKU."""
    return not products or any(not str(product.get("sku") or "").strip() for product in products)


def variation_attributes(product: dict[str, Any]) -> list[dict[str, str]]:
    attributes: list[dict[str, str]] = []
    for value in product.get("property_values") or []:
        name = value.get("property_name") or str(value.get("property_id") or "Option")
        values = value.get("values") or []
        if values:
            attributes.append({"name": str(name), "option": str(values[0])})
    return attributes


def listing_to_preview(item: dict[str, Any]) -> dict[str, Any]:
    listing = item["listing"]
    inventory = item["inventory"]
    images = item.get("images") or []
    analysis = item.get("analysis") or {}
    listing_id = listing["listing_id"]
    products = inventory_products(inventory)
    is_variable = len(products) > 1
    first_product = products[0] if products else {}
    first_offering = (first_product.get("offerings") or [{}])[0]
    base_price = money_to_string(first_offering.get("price") or listing.get("price"))
    base_stock = first_offering.get("quantity")
    missing_sku = has_missing_sku(products)
    product_payload = {
        "name": listing.get("title"),
        "type": "variable" if is_variable else "simple",
        "description": listing.get("description") or "",
        "sku": "" if is_variable else product_sku(first_product, listing_id),
        "regular_price": "" if is_variable else base_price,
        "manage_stock": False if is_variable else base_stock is not None,
        "stock_quantity": None if is_variable else base_stock,
        "images": [{"src": src} for src in (image_src(image) for image in images) if src],
        "meta_data": [
            {"key": "_etsy_listing_id", "value": str(listing_id)},
            {"key": "_etsy_url", "value": listing.get("url") or ""},
            {"key": "_m1_special_cases", "value": analysis.get("special_cases") or ""},
        ],
    }
    variations = []
    if is_variable:
        attributes: dict[str, set[str]] = {}
        for product in products:
            offering = (product.get("offerings") or [{}])[0]
            variations.append(
                {
                    "sku": product_sku(product, listing_id),
                    "regular_price": money_to_string(offering.get("price") or listing.get("price")),
                    "manage_stock": offering.get("quantity") is not None,
                    "stock_quantity": offering.get("quantity"),
                    "attributes": variation_attributes(product),
                    "meta_data": [
                        {"key": "_etsy_listing_id", "value": str(listing_id)},
                        {"key": "_etsy_product_id", "value": str(product.get("product_id") or "")},
                        {"key": "_etsy_offering_id", "value": str(offering.get("offering_id") or "")},
                    ],
                }
            )
            for attribute in variation_attributes(product):
                attributes.setdefault(attribute["name"], set()).add(attribute["option"])
        product_payload["attributes"] = [
            {"name": name, "visible": True, "variation": True, "options": sorted(options)}
            for name, options in sorted(attributes.items())
        ]

    return {
        "listing_id": listing_id,
        "source_title": listing.get("title"),
        "source_url": listing.get("url"),
        "special_cases": analysis.get("special_cases") or "",
        "has_missing_sku": missing_sku,
        "product": product_payload,
        "variations": variations,
    }


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1-080: Import-Preview aus Etsy-Analyse erzeugen, ohne WooCommerce zu schreiben."
    )
    parser.add_argument(
        "--analysis",
        default=str(output_dir("m1_etsy_analysis") / "latest.json"),
        help="Pfad zur Etsy-Analyse JSON.",
    )
    args = parser.parse_args()

    analysis_path = Path(args.analysis)
    analysis = read_json(analysis_path)
    previews = [listing_to_preview(item) for item in analysis.get("items") or []]
    summary_rows = [
        {
            "listing_id": item["listing_id"],
            "title": item["source_title"],
            "type": item["product"]["type"],
            "sku": item["product"].get("sku") or "",
            "variation_count": len(item["variations"]),
            "has_missing_sku": item["has_missing_sku"],
            "special_cases": item["special_cases"],
        }
        for item in previews
    ]

    out_dir = output_dir("m1_import_preview")
    stamp = timestamp()
    payload = {
        "source_analysis": str(analysis_path),
        "summary": {
            "product_count": len(previews),
            "missing_sku_count": sum(1 for item in previews if item["has_missing_sku"]),
            "write_safety": "Preview only. Dieses Script schreibt nicht nach WooCommerce.",
        },
        "items": previews,
    }
    write_json(out_dir / f"import-preview-{stamp}.json", payload)
    write_json(out_dir / "latest.json", payload)
    write_csv(
        out_dir / f"import-preview-{stamp}.csv",
        summary_rows,
        ["listing_id", "title", "type", "sku", "variation_count", "has_missing_sku", "special_cases"],
    )
    print(f"Import-Preview geschrieben: {out_dir / 'latest.json'}")
    print(f"Produkte: {payload['summary']['product_count']}")
    print(f"Fehlende SKUs: {payload['summary']['missing_sku_count']}")


if __name__ == "__main__":
    main_guard(run)
