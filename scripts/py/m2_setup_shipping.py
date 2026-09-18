from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from common import (
    DATA_DIR,
    add_common_args,
    etsy_get,
    load_config,
    load_etsy_config,
    load_etsy_token,
    load_woocommerce_config,
    main_guard,
    read_json,
    refresh_etsy_token_if_needed,
    resolve_etsy_shop_id,
    wc_get,
    wc_post,
    wc_put,
    write_json,
)


DEFAULT_ANALYSIS = DATA_DIR / "m1_etsy_analysis" / "latest.json"


def slugify(value: str) -> str:
    value = value.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")


def listing_id(product: dict[str, Any]) -> str | None:
    for meta in product.get("meta_data") or []:
        if meta.get("key") == "_etsy_listing_id":
            return str(meta.get("value"))
    return None


def ensure_category(wc: Any, name: str, slug: str) -> dict[str, Any]:
    categories = wc_get(wc, "products/categories", {"per_page": 100, "page": 1})
    for category in categories or []:
        if category.get("slug") == slug or str(category.get("name", "")).casefold() == name.casefold():
            return category
    return wc_post(wc, "products/categories", {"name": name, "slug": slug})


def run() -> None:
    parser = argparse.ArgumentParser(description="M2: Etsy-Versandprofile als WooCommerce-Versandklassen einrichten.")
    add_common_args(parser)
    parser.add_argument("--analysis", default=str(DEFAULT_ANALYSIS))
    args = parser.parse_args()
    config = load_config(args.config)
    etsy = load_etsy_config(config)
    token = refresh_etsy_token_if_needed(etsy, load_etsy_token())
    shop_id = resolve_etsy_shop_id(etsy, token)
    profiles = etsy_get(etsy, f"application/shops/{shop_id}/shipping-profiles", token=token).get("results", [])
    profile_by_id = {str(p["shipping_profile_id"]): p for p in profiles}
    wc = load_woocommerce_config(config)
    category_specs = {
        "6243": ("Farbverlaufsgarn / Bobbel", "farbverlaufsgarn-bobbel"),
        "6380": ("Garnschalen", "garnschalen"),
    }
    woo_categories = {
        taxonomy_id: ensure_category(wc, name, slug)
        for taxonomy_id, (name, slug) in category_specs.items()
    }
    classes = wc_get(wc, "products/shipping_classes", {"per_page": 100, "page": 1})
    class_by_slug = {str(item.get("slug")): item for item in classes or []}
    woo_classes: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        slug = slugify(str(profile["title"]))
        existing = class_by_slug.get(slug)
        if existing:
            woo_classes[str(profile["shipping_profile_id"])] = existing
            continue
        created = wc_post(
            wc,
            "products/shipping_classes",
            {
                "name": profile["title"],
                "slug": slug,
                "description": f"Etsy Versandprofil {profile['shipping_profile_id']}",
            },
        )
        woo_classes[str(profile["shipping_profile_id"])] = created

    products = wc_get(wc, "products", {"per_page": 100, "page": 1})
    products_by_listing = {listing_id(product): product for product in products if listing_id(product)}
    analysis = read_json(Path(args.analysis))
    updated = 0
    unmatched: list[str] = []
    for item in analysis.get("items") or []:
        listing = item["listing"]
        listing_key = str(listing["listing_id"])
        product = products_by_listing.get(listing_key)
        profile_key = str(listing.get("shipping_profile_id") or "")
        shipping_class = woo_classes.get(profile_key)
        profile = profile_by_id.get(profile_key)
        taxonomy_key = str(listing.get("taxonomy_id") or "")
        category = woo_categories.get(taxonomy_key)
        if not product or not shipping_class or not profile or not category:
            unmatched.append(listing_key)
            continue
        payload = {
            "shipping_class": shipping_class.get("slug") or slugify(str(profile["title"])),
            "categories": [{"id": category["id"]}],
            "meta_data": [
                {"key": "_etsy_shipping_profile_id", "value": profile_key},
                {"key": "_etsy_shipping_profile_title", "value": profile["title"]},
                {"key": "_etsy_return_policy_id", "value": str(listing.get("return_policy_id") or "")},
                {"key": "_etsy_taxonomy_id", "value": taxonomy_key},
                {"key": "_etsy_taxonomy_name", "value": category["name"]},
            ],
        }
        wc_put(wc, f"products/{product['id']}", payload)
        updated += 1
    report = {
        "shop_id": shop_id,
        "shipping_classes": [
            {"etsy_profile_id": key, "name": value.get("name"), "slug": value.get("slug"), "id": value.get("id")}
            for key, value in sorted(woo_classes.items())
        ],
        "categories": [
            {"etsy_taxonomy_id": key, "name": value.get("name"), "slug": value.get("slug"), "id": value.get("id")}
            for key, value in sorted(woo_categories.items())
        ],
        "products_updated": updated,
        "unmatched_listing_ids": unmatched,
    }
    out = DATA_DIR / "m2_shipping" / "latest.json"
    write_json(out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Report: {out}")


if __name__ == "__main__":
    main_guard(run)
