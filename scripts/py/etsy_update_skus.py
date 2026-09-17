from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Any

from common import (
    add_common_args,
    etsy_api_key_header,
    etsy_headers,
    load_config,
    load_etsy_config,
    load_etsy_token,
    read_json,
    request_json,
    timestamp,
    write_json,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANALYSIS = PROJECT_ROOT / "data/m1_etsy_analysis/latest.json"
NAME_CODES = {
    "GOLDMARIE": "GM",
    "BLUE LEMONADE": "BL",
    "EINZELSTÜCK": "ES",
    "WEINLAUB": "WL",
    "PHOENIXTRAUM": "PT",
    "GREY VELVET": "GV",
}
GRADIENT_CODES = (
    (re.compile(r"tuch(?:wicklung|verlauf)", re.I), "TV"),
    (re.compile(r"gemischt", re.I), "GV"),
    (re.compile(r"verr[üu]ckt", re.I), "VV"),
    (re.compile(r"sanft", re.I), "SV"),
    (re.compile(r"normal", re.I), "NV"),
)


def listing_text(item: dict[str, Any]) -> str:
    listing = item["listing"]
    return f"{listing.get('title', '')} {listing.get('description', '')}"


def bobbel_name_code(item: dict[str, Any]) -> str | None:
    title = str(item["listing"].get("title") or "")
    first = title.split("|", 1)[0].strip().upper()
    if first in NAME_CODES:
        return NAME_CODES[first]
    if "BOBBEL" in title.upper() or "FARBVERLAUFSGARN" in title.upper():
        return None
    return None


def length_code(item: dict[str, Any]) -> str | None:
    text = listing_text(item)
    match = re.search(r"(\d+)\s*[mM]", text)
    if not match:
        return None
    values = re.findall(r"\d+", match.group(0))
    # For titles such as 2x225m use the total running length.
    prefix = text[max(0, match.start() - 8) : match.start()]
    multiplier = re.search(r"(\d+)\s*x\s*$", prefix, re.I)
    value = int(match.group(1)) * (int(multiplier.group(1)) if multiplier else 1)
    return str(value)


def gradient_code(item: dict[str, Any], product: dict[str, Any]) -> str | None:
    text = f"{listing_text(item)} {product.get('property_values') or ''}"
    for pattern, code in GRADIENT_CODES:
        if pattern.search(text):
            return code
    return None


def is_bobbel(item: dict[str, Any]) -> bool:
    title = str(item["listing"].get("title") or "").lower()
    return "bobbel" in title or "farbverlaufsgarn" in title


def plan_skus(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    existing: Counter[str] = Counter()
    for item in analysis.get("items") or []:
        for product in item["inventory"].get("products") or []:
            sku = str(product.get("sku") or "").strip()
            if sku:
                existing[sku] += 1

    generic_number = 0
    used = set(existing)
    duplicate_seen: Counter[str] = Counter()
    generic_codes: dict[int, str] = {}
    changes: list[dict[str, Any]] = []
    for item in analysis.get("items") or []:
        if not is_bobbel(item):
            continue
        name = bobbel_name_code(item)
        length = length_code(item)
        if not length:
            continue
        listing_id = int(item["listing"]["listing_id"])
        for product in item["inventory"].get("products") or []:
            old = str(product.get("sku") or "").strip()
            if old and existing[old] == 1:
                continue
            if old and existing[old] > 1:
                duplicate_seen[old] += 1
                if duplicate_seen[old] == 1:
                    continue
            if name:
                base_name = name
            else:
                if listing_id not in generic_codes:
                    generic_number += 1
                    if generic_number > 99:
                        raise RuntimeError("Mehr als 99 namenlose Bobbel benoetigen eine neue Regel.")
                    generic_codes[listing_id] = f"{generic_number:02d}"
                base_name = generic_codes[listing_id]
            gradient = gradient_code(item, product)
            if not gradient:
                continue
            candidate = f"{base_name}-{length}-{gradient}"
            suffix = 1
            while candidate in used:
                suffix += 1
                candidate = f"{base_name}-{length}-{gradient}-{suffix}"
            used.add(candidate)
            changes.append(
                {
                    "listing_id": item["listing"]["listing_id"],
                    "product_id": product["product_id"],
                    "old_sku": old,
                    "new_sku": candidate,
                    "title": item["listing"].get("title"),
                }
            )
    return changes


def apply_changes(config: Any, analysis: dict[str, Any], changes: list[dict[str, Any]]) -> None:
    etsy = load_etsy_config(config)
    token = load_etsy_token()
    by_listing = {item["listing"]["listing_id"]: item for item in analysis.get("items") or []}
    for listing_id in sorted({change["listing_id"] for change in changes}):
        item = by_listing[listing_id]
        products = item["inventory"].get("products") or []
        replacement = {change["product_id"]: change["new_sku"] for change in changes if change["listing_id"] == listing_id}
        payload = {
            "products": [inventory_product_payload(product, replacement.get(product["product_id"])) for product in products],
            "price_on_property": item["inventory"].get("price_on_property") or [],
            "quantity_on_property": item["inventory"].get("quantity_on_property") or [],
            "sku_on_property": sku_on_properties(item["inventory"], products, replacement),
            "readiness_state_on_property": item["inventory"].get("readiness_state_on_property") or [],
        }
        request_json(
            "PUT",
            f"https://api.etsy.com/v3/application/listings/{listing_id}/inventory",
            expected=(200,),
            json=payload,
            headers=etsy_headers(etsy, token),
        )


def inventory_product_payload(product: dict[str, Any], replacement_sku: str | None = None) -> dict[str, Any]:
    """Convert Etsy's inventory response shape to the update request shape."""
    offerings = []
    for offering in product.get("offerings") or []:
        price = offering.get("price")
        if isinstance(price, dict):
            price = float(price.get("amount", 0)) / float(price.get("divisor") or 100)
        offerings.append(
            {
                "price": price,
                "quantity": offering.get("quantity", 0),
                "is_enabled": offering.get("is_enabled", True),
                "readiness_state_id": offering.get("readiness_state_id"),
            }
        )
    properties = []
    for prop in product.get("property_values") or []:
        properties.append(
            {
                "property_id": prop.get("property_id"),
                "value_ids": prop.get("value_ids") or [],
                "scale_id": prop.get("scale_id"),
                "property_name": prop.get("property_name"),
                "values": prop.get("values") or [],
            }
        )
    return {
        "sku": replacement_sku if replacement_sku is not None else product.get("sku") or "",
        "offerings": offerings,
        "property_values": properties,
    }


def sku_on_properties(
    inventory: dict[str, Any], products: list[dict[str, Any]], replacement: dict[int, str]
) -> list[int]:
    current = inventory.get("sku_on_property") or []
    if current:
        return current
    skus = [replacement.get(product["product_id"], product.get("sku") or "") for product in products]
    if len(products) < 2 or len(set(skus)) < 2:
        return []
    property_ids: list[int] = []
    for index in range(len((products[0].get("property_values") or []))):
        values = []
        for product in products:
            properties = product.get("property_values") or []
            prop = properties[index] if index < len(properties) else {}
            values.append((prop.get("property_id"), tuple(prop.get("value_ids") or []), tuple(prop.get("values") or [])))
        if len(set(values)) > 1 and values[0][0] is not None:
            property_ids.append(int(values[0][0]))
    return property_ids


def run() -> None:
    parser = argparse.ArgumentParser(description="Eindeutige Bobbel-SKUs nach dem M1-Schema vergeben.")
    add_common_args(parser)
    parser.add_argument("--analysis", default=str(DEFAULT_ANALYSIS))
    parser.add_argument("--apply", action="store_true", help="SKUs tatsaechlich nach Etsy schreiben.")
    args = parser.parse_args()
    config = load_config(args.config)
    analysis = read_json(Path(args.analysis))
    changes = plan_skus(analysis)
    report = {"generated_at": timestamp(), "applied": args.apply, "changes": changes}
    output = PROJECT_ROOT / "data/m1_sku_plan" / ("latest-applied.json" if args.apply else "latest.json")
    if args.apply:
        apply_changes(config, analysis, changes)
    write_json(output, report)
    print(f"SKU-Aenderungen: {len(changes)}")
    for change in changes:
        print(f"{change['listing_id']} / {change['product_id']}: {change['old_sku'] or '<leer>'} -> {change['new_sku']}")
    print(f"Plan geschrieben: {output}")


if __name__ == "__main__":
    run()
