# M2-010 Persistente Mapping-Tabelle

Status: umgesetzt als SQLite-Basis

## Ziel

Die Integration braucht eine persistente Zuordnung zwischen WooCommerce-Produkten bzw. Varianten und Etsy-Listings bzw. Etsy-Inventory-IDs.

Die SKU bleibt der fachliche Schluessel. WooCommerce- und Etsy-IDs werden als technische Verknuepfung gespeichert.

## Speicherort

Die lokale Mapping-Datenbank wird standardmaessig hier angelegt:

```text
data/m2_mapping/mapping.sqlite3
```

`data/` ist per `.gitignore` ausgeschlossen. Versioniert werden nur Schema, Skript und Dokumentation.

## Initialisierung

```bash
python scripts/py/m2_mapping_db.py --init
```

Zusammenfassung anzeigen:

```bash
python scripts/py/m2_mapping_db.py --summary
```

Optional ein manuelles Mapping anlegen:

```bash
python scripts/py/m2_mapping_db.py --add-sku MRS-EXAMPLE-01 --product-kind simple --sync-status draft
```

## Datenmodell

### `product_mapping`

| Feld | Zweck |
| --- | --- |
| `id` | Interner Primaerschluessel |
| `sku` | Fachlicher Schluessel, case-insensitive eindeutig |
| `product_kind` | `simple`, `variable_parent`, `variation` |
| `woocommerce_product_id` | WooCommerce Product ID |
| `woocommerce_variation_id` | WooCommerce Variation ID |
| `etsy_listing_id` | Etsy Listing ID |
| `etsy_product_id` | Etsy Inventory Product ID |
| `etsy_offering_id` | Etsy Inventory Offering ID |
| `sync_status` | `draft`, `linked`, `needs_review`, `blocked`, `archived` |
| `review_reason` | Grund fuer manuelle Pruefung |
| `last_seen_source` | `manual`, `woocommerce`, `etsy`, `import_preview`, `sync` |
| `created_at` | Erstellzeitpunkt |
| `updated_at` | Letzte Aenderung |

### `mapping_event`

Historientabelle fuer Mapping-Aenderungen und Sync-Ereignisse.

| Feld | Zweck |
| --- | --- |
| `mapping_id` | Optionaler Bezug auf `product_mapping.id` |
| `event_type` | z. B. `created`, `linked`, `needs_review`, `sync_success`, `sync_error` |
| `source` | Quelle des Ereignisses |
| `message` | Kurzer lesbarer Hinweis |
| `payload_json` | Optionales Roh-/Detailpayload als JSON-Text |
| `created_at` | Ereigniszeitpunkt |

### `sync_run`

Vorgesehene Tabelle fuer spaetere Sync-Laeufe und Idempotenz.

| Feld | Zweck |
| --- | --- |
| `direction` | Sync-Richtung, z. B. `woocommerce_to_etsy` oder `stock` |
| `status` | `started`, `success`, `partial`, `error` |
| `idempotency_key` | Eindeutiger Schluessel fuer wiederholbare Verarbeitung |
| `started_at` | Startzeitpunkt |
| `finished_at` | Endzeitpunkt |
| `summary_json` | Zusammenfassung als JSON-Text |
| `error_message` | Fehlertext bei Abbruch |

## Eindeutigkeit

Das Schema erzwingt:

- SKU ist case-insensitive eindeutig.
- WooCommerce Product ID ist eindeutig fuer Parent-/Simple-Produkte.
- WooCommerce Variation ID ist eindeutig.
- Etsy-Kombination aus Listing ID, Inventory Product ID und Offering ID ist eindeutig, sobald vorhanden.
- `sync_run.idempotency_key` ist eindeutig, sobald vorhanden.

## SKU-Validierung

Das Skript akzeptiert fuer manuelle Eintraege nur SKUs mit:

```text
Buchstaben, Zahlen, Punkt, Unterstrich, Bindestrich
```

Fuehrende oder folgende Leerzeichen sind ungueltig. Die eigentliche fachliche SKU-Vergabe bleibt Teil der Import-Preview bzw. manuellen Review.

## Statusregeln

| Status | Bedeutung |
| --- | --- |
| `draft` | Mapping vorbereitet, noch nicht vollstaendig verknuepft |
| `linked` | WooCommerce und Etsy sind eindeutig verknuepft |
| `needs_review` | Manuelle Pruefung erforderlich |
| `blocked` | Automatische Verarbeitung gesperrt |
| `archived` | Historischer Eintrag, nicht mehr aktiv |

## Bezug zu M1-Entscheidungen

- Bundles werden in M1 nicht technisch modelliert. Falls spaeter echte Bundle-Logik noetig wird, kann sie als Erweiterung auf dem Mapping aufsetzen.
- Made-to-Order bleibt in M1 normale Produkt-/Variantenlogik mit Bestandspuffer und abweichendem Versandprofil.
- Personalisierung bleibt Order-Line-Meta und erzeugt keine neue SKU.

## Naechster Schritt

Wenn Etsy-Zugriff funktioniert, wird die Import-Preview so erweitert, dass sie Mapping-Eintraege als `draft`, `linked`, `needs_review` oder `blocked` vorschlaegt. Der echte Schreibvorgang nach WooCommerce kann danach die erzeugten WooCommerce-IDs in `product_mapping` uebernehmen.
