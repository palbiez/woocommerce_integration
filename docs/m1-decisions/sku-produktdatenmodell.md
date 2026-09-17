# M1-040 SKU- und Produktdatenmodell

## Verbindliche SKU-Syntax fuer Bobbel

Fuer Bobbel wird folgende Syntax verwendet:

```text
<Namecode>-<Lauflänge in Metern>-<Verlaufsart>[-<Duplikatnummer>]
```

Namecodes bestehen aus zwei Grossbuchstaben, zum Beispiel `GM` fuer GoldMarie, `BL` fuer Blue Lemonade und `ES` fuer EINZELSTÜCK. Weitere bekannte Namen werden ebenfalls stabil auf zwei Buchstaben abgebildet, z. B. `WL` fuer Weinlaub, `PT` fuer Phoenixtraum und `GV` fuer Grey Velvet. Wenn kein Name vorhanden ist, wird eine laufende Nummer von `01` bis `99` verwendet.

Verlaufsarten:

| Code | Bedeutung |
| --- | --- |
| `NV` | normaler Verlauf |
| `SV` | sanfter Verlauf |
| `VV` | verrückter Verlauf |
| `GV` | gemischter Verlauf |
| `TV` | Tuchverlauf/Tuchwicklung |

Die Lauflänge wird in Metern angegeben; bei Angaben wie `2x225m` wird die Gesamtlaenge `450` verwendet. Bei einer echten Kollision wird eine Duplikatnummer angehaengt, z. B. `ES-1500-SV-2`.

Die Syntax gilt fuer Bobbel und Bobbel-Varianten. Andere Produktgruppen, aktuell insbesondere Garnschalen, erhalten keine automatisch erfundene Bobbel-SKU; dafuer wird bei Bedarf eine eigene Produktgruppen-Syntax beschlossen.

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
- Bundles werden in M1 nicht technisch modelliert; betroffene Artikel bleiben Einzelprodukte, Preisvorteile laufen ueber Gutschein/Rabatt.
- Personalisierung veraendert nicht die SKU, sondern wird als Bestellpositions-Metadaten gespeichert.
- Made-to-Order veraendert nicht die SKU; in M1 steckt die laengere Bearbeitungszeit im abweichenden Versandprofil.

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

### Bundles und Sets

Regel:

```text
In M1 keine technische Bundle-SKU.
Artikel bleiben einzelne Produkte; Preisvorteile laufen ueber Gutschein/Rabatt.
```

Beispiel:

```text
Produkt 1: MRS-CARD-BABY
Produkt 2: MRS-STICKER-HEART
Rabatt: Gutschein oder Preisaktion
```

Pflicht:

- Keine zusaetzliche Bundle-SKU fuer M1 erzeugen.
- Bestand bleibt auf Einzelprodukt-/Variantenebene.
- Etsy-Set- oder Bundle-Kandidaten werden spaeter in der Import-Preview als `needs_review` markiert, falls sie nicht sauber als Einzelprodukte plus Rabatt abbildbar sind.

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
SKU bleibt Artikel-SKU; Made-to-Order wird in M1 ueber Versandprofil und Bestandspuffer behandelt.
```

Pflicht:

- Made-to-Order erzeugt keine neue SKU.
- Laengere Bearbeitungszeit steckt in einem abweichenden Versandprofil.
- Bestand kann als Puffer gefuehrt werden, z. B. 10, und nach Versand wieder erhoeht werden.
- Keine Pflichtfelder fuer `production_group`, `availability_policy` oder Produktionsstatus in M1.

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
| `bundle_sku` | string | spaeter optional | Verkaufs-SKU fuer echte Bundle-Logik |
| `component_sku` | string | spaeter optional | Komponenten-SKU |
| `quantity` | decimal | spaeter optional | Menge pro Bundle |
| `stock_policy` | enum | spaeter optional | `reduce_component_stock`, `virtual_only` |

Hinweis: Diese Tabelle wird in M1 nicht umgesetzt. Sie bleibt nur als spaetere Erweiterungsoption, falls echte Bundle-Logik notwendig wird.

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
- [ ] Bundle-/Set-Kandidaten sind als Einzelprodukte plus Rabatt abbildbar oder als `needs_review` markiert.
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
- [ ] Bundles werden in M1 nicht technisch modelliert; Preisvorteile laufen ueber Gutschein/Rabatt.
- [ ] Personalisierung bleibt Order-Line-Meta und erzeugt keine SKU.
- [ ] Made-to-Order wird in M1 ueber abweichendes Versandprofil und Bestandspuffer abgebildet, nicht ueber separate SKU je Bestellung.

## Offene Fragen

- Gibt es bereits ein existierendes SKU-Schema, das uebernommen werden soll?
- Sollen SKUs sprechend sein oder nur fortlaufende Artikelnummern?
- Gibt es spaeter echte Bundle-Faelle, die nicht mit Einzelprodukten plus Rabatt abbildbar sind?
- Welche Personalisierungsfelder kommen aktuell in Etsy vor?
- Gibt es Made-to-Order-Produkte mit echtem Komponentenbestand?

## Naechster Schritt

Nach Entscheidung:

1. Etsy-Analyse/CSV um SKU- und Sonderfallspalten pruefen.
2. Fehlende SKUs manuell vergeben.
3. Mapping-Datei oder Datenbankschema fuer `M2-010` ableiten.
