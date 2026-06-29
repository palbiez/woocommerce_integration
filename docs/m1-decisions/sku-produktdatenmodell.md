# M1-040 SKU- und Produktdatenmodell

Status: vorbereitet zur Entscheidung

## Ziel

Ein stabiles Modell fuer Produkte, Varianten, SKUs, Bundles, Personalisierung und Made-to-Order festlegen, bevor Etsy-Daten nach WooCommerce importiert werden.

Leitentscheidung:

> WooCommerce wird fuehrendes System. Etsy wird ueber stabile IDs und SKUs angebunden.

## Empfehlung

Empfohlener Ansatz: **SKU als fachlicher stabiler Schluessel, IDs als technische Verknuepfung, Sonderlogik in eigener Mapping-Tabelle.**

Das bedeutet:

- Jede verkaufbare Einheit bekommt genau eine stabile SKU.
- WooCommerce Product ID und Variation ID werden nicht fachlich interpretiert, sondern nur technisch gespeichert.
- Etsy Listing ID, Inventory Product ID und Offering ID werden dauerhaft gemappt.
- Bundles bekommen eigene Verkaufs-SKU plus separate Komponentenliste.
- Personalisierung veraendert nicht die SKU, sondern wird als Bestellpositions-Metadaten gespeichert.
- Made-to-Order veraendert nicht die SKU, sondern bekommt eigene Produktions-/Lieferzeitfelder.

## Warum diese Entscheidung sinnvoll ist

Bei Etsy/WooCommerce-Sync ist die SKU der einzige Schluessel, den Menschen, Exportdaten und beide Systeme sinnvoll gemeinsam verwenden koennen. IDs sind stabil, aber systemspezifisch. Deshalb sollten IDs gespeichert werden, aber nicht als fachliche Artikelnummer dienen.

Mit 25 bis 100 Produkten ist ein explizites Mapping einfacher und sicherer als implizite Heuristiken. Es verhindert doppelte Listings, vereinfacht Replays und macht Konflikte sichtbar.

## SKU-Regeln

### Einfache Produkte

Regel:

```text
SKU = eindeutige Artikelnummer der verkaufbaren Einheit
```

Beispiel:

```text
MRS-PRINT-A4-ROSE
```

Pflicht:

- SKU darf nach Import nicht still geaendert werden.
- Leere Etsy-SKUs werden vor Import markiert und manuell vergeben.
- SKU ist case-insensitive eindeutig zu behandeln.

### Varianten

Regel:

```text
Parent-Produkt: optional sprechende Parent-SKU
Jede Variante: eigene verkaufbare SKU
```

Beispiel:

```text
Parent: MRS-SHIRT-HEART
Variante S Weiss: MRS-SHIRT-HEART-WHT-S
Variante M Weiss: MRS-SHIRT-HEART-WHT-M
```

Pflicht:

- Bestand wird auf Variantenebene gefuehrt, wenn Varianten physisch unterschiedlich sind.
- Variantenattribute werden normalisiert, z. B. `Farbe`, `Groesse`, `Material`.
- Eine Variante ohne SKU darf nicht automatisch importiert werden.

### Bundles

Regel:

```text
Bundle = eigene Verkaufs-SKU
Komponenten = eigene Komponenten-SKUs mit Menge
```

Beispiel:

```text
Bundle-SKU: MRS-SET-BABY-01
Komponenten:
- MRS-CARD-BABY x 1
- MRS-STICKER-HEART x 2
```

Pflicht:

- Bundle-SKU darf nicht gleichzeitig als physischer Komponentenartikel verwendet werden.
- Komponentenbestand wird spaeter beim Bestandsabgleich separat reduziert.
- Bundle-Zusammensetzung gehoert in die eigene Integration bzw. Mapping-Tabelle, nicht nur in Beschreibungstext.

### Personalisierte Produkte

Regel:

```text
SKU beschreibt das Basisprodukt, Personalisierung ist Bestellpositions-Metadatum.
```

Beispiel:

```text
SKU: MRS-MUG-NAME-01
Personalisierung:
- name = "Mia"
- farbe = "Rosa"
- hinweis = "Bitte Geschenkverpackung"
```

Pflicht:

- Personalisierungswerte duerfen keine neue SKU erzeugen.
- Pflichtfelder muessen vor Checkout validiert werden.
- Daten muessen in WooCommerce Order Line Item Meta sichtbar sein.
- Daten muessen spaeter an Etsy/Dolibarr/Produktion uebergeben werden koennen.

### Made-to-Order

Regel:

```text
SKU bleibt Artikel-SKU; Produktionsstatus und Lieferzeit sind separate Felder.
```

Pflicht:

- Made-to-Order wird nicht als unendlicher Lagerbestand behandelt.
- Lieferzeit/Produktionszeit wird als Produkt- oder Varianten-Metadatum gepflegt.
- Bestellungen erhalten spaeter Produktionsstatus, z. B. `new`, `in_production`, `ready_to_ship`.

## Datenmodell

### Produkt-Mapping

| Feld | Typ | Pflicht | Zweck |
| --- | --- | --- | --- |
| `sku` | string | ja | Fachlicher Schluessel |
| `woocommerce_product_id` | integer | ja nach Import | WooCommerce Produkt |
| `woocommerce_variation_id` | integer/null | bei Varianten | WooCommerce Variante |
| `etsy_listing_id` | integer/null | nach Etsy-Link | Etsy Listing |
| `etsy_product_id` | integer/null | bei Etsy Inventory | Etsy Inventory Product |
| `etsy_offering_id` | integer/null | bei Etsy Inventory | Etsy Offering |
| `sync_status` | enum | ja | `draft`, `linked`, `needs_review`, `blocked` |
| `last_seen_source` | enum | ja | `etsy`, `woocommerce`, `manual` |

### Bundle-Komponenten

| Feld | Typ | Pflicht | Zweck |
| --- | --- | --- | --- |
| `bundle_sku` | string | ja | Verkaufs-SKU |
| `component_sku` | string | ja | Komponenten-SKU |
| `quantity` | decimal | ja | Menge pro Bundle |
| `stock_policy` | enum | ja | `reduce_component_stock`, `virtual_only` |

### Personalisierungsfelder

| Feld | Typ | Pflicht | Zweck |
| --- | --- | --- | --- |
| `sku` | string | ja | Basisprodukt |
| `field_key` | string | ja | Technischer Feldname |
| `label` | string | ja | Anzeige im Shop |
| `type` | enum | ja | `text`, `textarea`, `select`, `checkbox`, `file` |
| `required` | boolean | ja | Pflichtfeld |
| `export_target` | enum | ja | `etsy`, `dolibarr`, `production`, `none` |

## Import-Regeln

Vor WooCommerce-Schreiboperationen:

- [ ] Jede verkaufbare Einheit hat eine SKU.
- [ ] Doppelte SKUs sind bereinigt.
- [ ] Variantenattribute sind normalisiert.
- [ ] Bundle-Kandidaten sind markiert.
- [ ] Personalisierte Produkte sind markiert.
- [ ] Made-to-Order-Kandidaten sind markiert.

Wenn Etsy-Daten unvollstaendig sind:

- Produkt nicht automatisch importieren.
- In Import-Preview als `blocked_missing_sku` oder `needs_mapping_decision` markieren.
- Manuelle Entscheidung dokumentieren.

## Entscheidungsvorlage

Bitte diese Punkte bestaetigen oder anpassen:

- [ ] SKU ist der fachliche Primaerschluessel fuer Sync und Dublettenpruefung.
- [ ] WooCommerce/Etsy IDs werden nur als technische Mapping-IDs gespeichert.
- [ ] Jede Variante bekommt eine eigene SKU.
- [ ] Bundles bekommen eigene Verkaufs-SKU plus Komponentenliste.
- [ ] Personalisierung bleibt Order-Line-Meta und erzeugt keine SKU.
- [ ] Made-to-Order wird ueber Produktions-/Lieferzeitfelder abgebildet, nicht ueber separate SKU je Bestellung.

## Offene Fragen

- Gibt es bereits ein existierendes SKU-Schema, das uebernommen werden soll?
- Sollen SKUs sprechend sein oder nur fortlaufende Artikelnummern?
- Muessen Bundle-Komponenten einzeln in WooCommerce sichtbar sein?
- Welche Personalisierungsfelder kommen aktuell in Etsy vor?
- Gibt es Made-to-Order-Produkte mit echtem Komponentenbestand?

## Naechster Schritt

Nach Entscheidung:

1. Etsy-Analyse/CSV um SKU- und Sonderfallspalten pruefen.
2. Fehlende SKUs manuell vergeben.
3. Mapping-Datei oder Datenbankschema fuer `M2-010` ableiten.
