from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
from typing import Any

from common import DATA_DIR, ScriptError, ensure_dir, main_guard


DEFAULT_DB = DATA_DIR / "m2_mapping" / "mapping.sqlite3"
SCHEMA_VERSION = 1
SKU_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]*$", re.IGNORECASE)


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS schema_meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS product_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT NOT NULL,
        product_kind TEXT NOT NULL CHECK (product_kind IN ('simple', 'variable_parent', 'variation')),
        woocommerce_product_id INTEGER,
        woocommerce_variation_id INTEGER,
        etsy_listing_id INTEGER,
        etsy_product_id INTEGER,
        etsy_offering_id INTEGER,
        sync_status TEXT NOT NULL DEFAULT 'draft'
            CHECK (sync_status IN ('draft', 'linked', 'needs_review', 'blocked', 'archived')),
        review_reason TEXT,
        last_seen_source TEXT NOT NULL DEFAULT 'manual'
            CHECK (last_seen_source IN ('manual', 'woocommerce', 'etsy', 'import_preview', 'sync')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (length(trim(sku)) > 0),
        CHECK (
            product_kind != 'variation'
            OR woocommerce_variation_id IS NULL
            OR woocommerce_product_id IS NOT NULL
        )
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_product_mapping_sku_nocase
    ON product_mapping (lower(sku))
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_product_mapping_wc_product
    ON product_mapping (woocommerce_product_id)
    WHERE woocommerce_product_id IS NOT NULL AND woocommerce_variation_id IS NULL
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_product_mapping_wc_variation
    ON product_mapping (woocommerce_variation_id)
    WHERE woocommerce_variation_id IS NOT NULL
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_product_mapping_etsy_listing_product_offering
    ON product_mapping (
        etsy_listing_id,
        coalesce(etsy_product_id, -1),
        coalesce(etsy_offering_id, -1)
    )
    WHERE etsy_listing_id IS NOT NULL
    """,
    """
    CREATE TRIGGER IF NOT EXISTS trg_product_mapping_updated_at
    AFTER UPDATE ON product_mapping
    FOR EACH ROW
    BEGIN
        UPDATE product_mapping
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.id;
    END
    """,
    """
    CREATE TABLE IF NOT EXISTS mapping_event (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mapping_id INTEGER,
        event_type TEXT NOT NULL CHECK (
            event_type IN (
                'created',
                'updated',
                'linked',
                'blocked',
                'needs_review',
                'archived',
                'sync_attempt',
                'sync_success',
                'sync_error'
            )
        ),
        source TEXT NOT NULL CHECK (
            source IN ('manual', 'woocommerce', 'etsy', 'import_preview', 'sync', 'system')
        ),
        message TEXT,
        payload_json TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (mapping_id) REFERENCES product_mapping(id)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_mapping_event_mapping_created
    ON mapping_event (mapping_id, created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS sync_run (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        direction TEXT NOT NULL CHECK (
            direction IN ('woocommerce_to_etsy', 'etsy_to_woocommerce', 'orders_etsy_to_woocommerce', 'stock')
        ),
        status TEXT NOT NULL DEFAULT 'started'
            CHECK (status IN ('started', 'success', 'partial', 'error')),
        idempotency_key TEXT,
        started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        finished_at TEXT,
        summary_json TEXT,
        error_message TEXT
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS ux_sync_run_idempotency_key
    ON sync_run (idempotency_key)
    WHERE idempotency_key IS NOT NULL
    """,
]


def validate_sku(sku: str) -> str:
    normalized = sku.strip()
    if not normalized:
        raise ScriptError("SKU darf nicht leer sein.")
    if normalized != sku:
        raise ScriptError(f"SKU enthaelt fuehrende oder folgende Leerzeichen: {sku!r}")
    if not SKU_PATTERN.match(normalized):
        raise ScriptError(
            f"Ungueltige SKU {sku!r}. Erlaubt sind Buchstaben, Zahlen, Punkt, Unterstrich und Bindestrich."
        )
    return normalized


def connect(db_path: Path) -> sqlite3.Connection:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.execute(
            """
            INSERT INTO schema_meta (key, value)
            VALUES ('schema_version', ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(SCHEMA_VERSION),),
        )
        conn.execute(
            """
            INSERT INTO mapping_event (event_type, source, message)
            VALUES ('created', 'system', ?)
            """,
            (f"Mapping-Datenbank initialisiert oder migriert auf Version {SCHEMA_VERSION}.",),
        )


def add_mapping(
    db_path: Path,
    *,
    sku: str,
    product_kind: str,
    woocommerce_product_id: int | None,
    woocommerce_variation_id: int | None,
    etsy_listing_id: int | None,
    etsy_product_id: int | None,
    etsy_offering_id: int | None,
    sync_status: str,
    review_reason: str | None,
    last_seen_source: str,
) -> None:
    validate_sku(sku)
    with connect(db_path) as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO product_mapping (
                    sku,
                    product_kind,
                    woocommerce_product_id,
                    woocommerce_variation_id,
                    etsy_listing_id,
                    etsy_product_id,
                    etsy_offering_id,
                    sync_status,
                    review_reason,
                    last_seen_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sku,
                    product_kind,
                    woocommerce_product_id,
                    woocommerce_variation_id,
                    etsy_listing_id,
                    etsy_product_id,
                    etsy_offering_id,
                    sync_status,
                    review_reason,
                    last_seen_source,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise ScriptError(f"Mapping konnte nicht angelegt werden: {exc}") from exc
        conn.execute(
            """
            INSERT INTO mapping_event (mapping_id, event_type, source, message)
            VALUES (?, 'created', ?, ?)
            """,
            (cursor.lastrowid, last_seen_source, f"Mapping fuer SKU {sku} angelegt."),
        )


def summary(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        raise ScriptError(f"Mapping-Datenbank existiert noch nicht: {db_path}")
    with connect(db_path) as conn:
        version = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        status_rows = conn.execute(
            """
            SELECT sync_status, count(*) AS count
            FROM product_mapping
            GROUP BY sync_status
            ORDER BY sync_status
            """
        ).fetchall()
        event_count = conn.execute("SELECT count(*) AS count FROM mapping_event").fetchone()
        return {
            "db_path": str(db_path),
            "schema_version": version["value"] if version else None,
            "mapping_count": sum(row["count"] for row in status_rows),
            "by_status": {row["sync_status"]: row["count"] for row in status_rows},
            "event_count": event_count["count"],
        }


def print_summary(data: dict[str, Any]) -> None:
    print(f"DB: {data['db_path']}")
    print(f"Schema-Version: {data['schema_version']}")
    print(f"Mappings: {data['mapping_count']}")
    print(f"Events: {data['event_count']}")
    if data["by_status"]:
        print("Status:")
        for status, count in data["by_status"].items():
            print(f"  {status}: {count}")


def parse_optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def run() -> None:
    parser = argparse.ArgumentParser(
        description="M2-010: Persistente Mapping-Datenbank fuer WooCommerce/Etsy initialisieren und pruefen."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Pfad zur SQLite-DB.")
    parser.add_argument("--init", action="store_true", help="Schema anlegen oder aktualisieren.")
    parser.add_argument("--summary", action="store_true", help="Kurze DB-Zusammenfassung ausgeben.")
    parser.add_argument("--add-sku", help="Test-/Manuell-Mapping fuer diese SKU anlegen.")
    parser.add_argument(
        "--product-kind",
        choices=("simple", "variable_parent", "variation"),
        default="simple",
    )
    parser.add_argument("--woocommerce-product-id")
    parser.add_argument("--woocommerce-variation-id")
    parser.add_argument("--etsy-listing-id")
    parser.add_argument("--etsy-product-id")
    parser.add_argument("--etsy-offering-id")
    parser.add_argument(
        "--sync-status",
        choices=("draft", "linked", "needs_review", "blocked", "archived"),
        default="draft",
    )
    parser.add_argument("--review-reason")
    parser.add_argument(
        "--last-seen-source",
        choices=("manual", "woocommerce", "etsy", "import_preview", "sync"),
        default="manual",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    if args.init:
        init_db(db_path)
        print(f"Mapping-Datenbank bereit: {db_path}")

    if args.add_sku:
        if not db_path.exists():
            init_db(db_path)
        add_mapping(
            db_path,
            sku=args.add_sku,
            product_kind=args.product_kind,
            woocommerce_product_id=parse_optional_int(args.woocommerce_product_id),
            woocommerce_variation_id=parse_optional_int(args.woocommerce_variation_id),
            etsy_listing_id=parse_optional_int(args.etsy_listing_id),
            etsy_product_id=parse_optional_int(args.etsy_product_id),
            etsy_offering_id=parse_optional_int(args.etsy_offering_id),
            sync_status=args.sync_status,
            review_reason=args.review_reason,
            last_seen_source=args.last_seen_source,
        )
        print(f"Mapping fuer SKU angelegt: {args.add_sku}")

    if args.summary or (not args.init and not args.add_sku):
        print_summary(summary(db_path))


if __name__ == "__main__":
    main_guard(run)
