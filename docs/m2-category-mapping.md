# M2-020 Etsy-Kategorie-, Attribut- und Template-Mapping

## Aktuelle Bestandsaufnahme

Die aktive Etsy-Analyse vom 18.09.2026 umfasst 35 Listings und zwei Etsy-Taxonomien:

| Etsy-Taxonomie | Anzahl | Produktgruppe |
| ---: | ---: | --- |
| `6243` | 32 | Farbverlaufsgarn/Bobbel |
| `6380` | 3 | Garnschalen |

Weitere wiederkehrende Etsy-Daten:

| Feld | Werte | Status |
| --- | --- | --- |
| `shipping_profile_id` | `280362699607` (25), `291679087672` (10) | Etsy-Profile erfasst, WooCommerce-Zuordnung offen |
| `return_policy_id` | `1398711496816` (32), `1407362359508` (3) | erfasst, Zuordnung offen |
| `when_made` | `2020_2026` (32), `made_to_order` (3) | erfasst |
| Personalisierung | 3 Listings | WooCommerce-Feld-/Checkout-Entscheidung offen |
| Bearbeitungszeit | Bobbel 1–2 Tage, Garnschalen 3–5 Tage | erfasst |

## Vorgeschlagenes WooCommerce-Mapping

Die Etsy-Taxonomie-ID wird als technische Referenz gespeichert. Die sichtbaren WooCommerce-Kategorien
sollten fachlich festgelegt und anschließend als stabile IDs in einer versionierten Mapping-Datei gepflegt werden:

```yaml
etsy_taxonomy:
  "6243": bobbel
  "6380": garnschale
```

Die Etsy-Versandprofile dürfen nicht automatisch nur anhand ihrer ID in WooCommerce-Versandzonen übersetzt
werden. Dafür muss festgelegt werden, welche WooCommerce-Versandklasse bzw. Versandzone den beiden Profilen
entspricht. Gleiches gilt für Rückgaberegeln.

## Template-Regeln

- Bobbel behalten SKU, Variantenattribute, Lauflänge und Verlaufsart als strukturierte Produktdaten.
- Garnschalen erhalten die Produktgruppe `Garnschale` und die Größeninformation in Zentimetern.
- Personalisierte Listings müssen im Checkout und in der WooCommerce-Bestellung als Order-Line-Meta erhalten bleiben.
- Etsy-Listing-ID, Taxonomie-ID, Versandprofil-ID und Rückgaberegel-ID werden als technische Produkt-Meta gespeichert.

## Offene Entscheidungen

1. Welche konkreten WooCommerce-Kategorien und IDs sollen für Bobbel und Garnschalen verwendet werden?
2. Welche WooCommerce-Versandklasse/Zonen entsprechen den beiden Etsy-Versandprofilen?
3. Soll die Etsy-Rückgaberegel nach WooCommerce übertragen werden oder bleibt sie Etsy-spezifisch?
4. Sollen Bearbeitungszeiten als Produktmeta, Versandklasse oder sichtbarer Lieferhinweis geführt werden?

Der technische Ist-Stand ist damit erfasst; die endgültige veröffentlichungsfähige Zuordnung bleibt bis zu diesen
Entscheidungen bewusst offen.
