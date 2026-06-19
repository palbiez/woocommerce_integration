from __future__ import annotations

import argparse
from typing import Any

from common import (
    add_common_args,
    load_config,
    load_woocommerce_config,
    main_guard,
    output_dir,
    timestamp,
    wc_get,
    write_json,
)


def summarize_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product.get("id"),
        "name": product.get("name"),
        "type": product.get("type"),
        "sku": product.get("sku"),
        "stock_status": product.get("stock_status"),
        "stock_quantity": product.get("stock_quantity"),
        "manage_stock": product.get("manage_stock"),
        "variation_count": len(product.get("variations") or []),
    }


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M1-010: WooCommerce REST API Zugriff fuer Produkte, Varianten, Bestand und Bestellungen testen."
    )
    add_common_args(parser)
    parser.add_argument("--per-page", type=int, default=5, help="Anzahl Testobjekte je Endpoint.")
    args = parser.parse_args()

    config = load_config(args.config)
    wc = load_woocommerce_config(config)

    products = wc_get(wc, "products", {"per_page": args.per_page, "page": 1})
    orders = wc_get(wc, "orders", {"per_page": args.per_page, "page": 1})

    selected_product = products[0] if products else None
    product_detail = None
    variations = []
    if selected_product:
        product_detail = wc_get(wc, f"products/{selected_product['id']}")
        if product_detail.get("type") == "variable":
            variations = wc_get(
                wc,
                f"products/{selected_product['id']}/variations",
                {"per_page": args.per_page, "page": 1},
            )

    report = {
        "base_url": wc.base_url,
        "checks": {
            "products_read": bool(products),
            "single_product_read": bool(product_detail),
            "variations_read": selected_product is None
            or product_detail.get("type") != "variable"
            or isinstance(variations, list),
            "stock_read": any("stock_status" in product for product in products),
            "orders_read": isinstance(orders, list),
            "auth_without_code_secrets": True,
        },
        "products": [summarize_product(product) for product in products],
        "selected_product": summarize_product(product_detail) if product_detail else None,
        "variations": [
            {
                "id": variation.get("id"),
                "sku": variation.get("sku"),
                "stock_status": variation.get("stock_status"),
                "stock_quantity": variation.get("stock_quantity"),
                "regular_price": variation.get("regular_price"),
            }
            for variation in variations
        ],
        "orders": [
            {
                "id": order.get("id"),
                "number": order.get("number"),
                "status": order.get("status"),
                "date_created": order.get("date_created"),
                "line_items": len(order.get("line_items") or []),
            }
            for order in orders
        ],
    }

    out = output_dir("m1_woocommerce_check") / f"woocommerce-api-check-{timestamp()}.json"
    write_json(out, report)
    print(f"WooCommerce API Check geschrieben: {out}")
    print(f"Produkte gelesen: {len(products)}")
    print(f"Bestellungen gelesen: {len(orders)}")


if __name__ == "__main__":
    main_guard(run)
