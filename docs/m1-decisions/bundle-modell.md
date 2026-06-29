# M1-060 Bundle-Modell in WooCommerce

Status: entschieden

## Entscheidung

Wie werden Bundles technisch in WooCommerce abgebildet?

Entscheidung: **In M1 werden keine technischen Bundles angelegt. Produkte bleiben einzelne verkaufbare WooCommerce-Produkte. Paket-/Set-Preise werden vorerst ueber Gutschein, Rabatt oder manuelle Preisaktion abgebildet.**

## Rahmenbedingung

Etsy erlaubt aktuell keinen verlaesslichen Zugriff auf die echten Listing-/Inventory-Daten. Gleichzeitig ist der erwartete Bundle-Umfang klein genug, dass eine eigene Bundle-/Komponentenlogik fuer M1 mehr Komplexitaet als Nutzen erzeugt.

Konsequenz:

- keine Bundle-Produkte jetzt manuell in WooCommerce anlegen
- keine Bundle-Komponenten-Tabelle fuer M1 umsetzen
- keine automatische Komponentenbestandsreduktion fuer Sets in M1 bauen
- Kunden kaufen die betroffenen Artikel als einzelne Produkte
- Preisvorteile werden ueber Gutschein, Rabattregel oder manuelle Preisreduktion abgebildet

## Begruendung

Die urspruengliche Bundle-Logik haette eigene Verkaufs-SKUs, Komponentenlisten, Bestandsregeln und spaetere Testfaelle benoetigt. Fuer den Start ist das nicht notwendig, wenn der praktische Fall auch mit zwei separaten Produkten und einem Rabatt geloest werden kann.

Damit bleibt M1 schlanker:

- weniger Datenmodell
- weniger Sync-Sonderfaelle
- weniger Risiko beim initialen WooCommerce-Import
- keine Abhaengigkeit von kostenpflichtigen Bundle-Plugins
- keine eigene Logik fuer Komponentenbestand

## Zielmodell fuer M1

### Produkte

Regel:

```text
Jeder Artikel bleibt ein normales Produkt bzw. eine normale Variante mit eigener SKU.
```

Beispiel:

```text
Produkt 1: MRS-CARD-BABY
Produkt 2: MRS-STICKER-HEART
Rabatt: Gutschein oder Preisaktion fuer gemeinsame Bestellung
```

Pflicht:

- Jedes verkaufbare Produkt braucht weiterhin eine stabile SKU.
- Es wird keine zusaetzliche Bundle-SKU erzeugt.
- Es wird keine Komponentenliste fuer diese Kombination gepflegt.

### Preis

Regel:

```text
Set-/Paketvorteile werden als Rabatt abgebildet.
```

Moegliche Umsetzung:

- WooCommerce-Gutschein
- zeitlich begrenzte Rabattaktion
- manuelle Preisreduktion
- spaeter optional Rabattregel-Plugin, falls Standard-Gutscheine nicht reichen

Pflicht:

- Rabattlogik darf keine neue SKU erzeugen.
- Preislogik fuer Etsy/WooCommerce wird spaeter in M2-040 konkret festgelegt.
- Automatische Etsy-Rabattabbildung wird erst geprueft, wenn Etsy-Zugriff funktioniert.

### Bestand

Regel:

```text
Bestand wird auf den einzelnen Produkten gefuehrt.
```

Pflicht:

- Beim Verkauf werden nur die tatsaechlich gekauften Einzelprodukte reduziert.
- Es gibt in M1 keine automatische Ableitung eines Bundle-Bestands.
- Keine separate Komponentenbestandslogik fuer Sets.

## Nicht-Ziele in M1

- kein WooCommerce-Bundle-Plugin
- keine Composite-/Grouped-Product-Logik als Startvoraussetzung
- keine eigene Bundle-Mapping-Tabelle
- keine automatische Komponentenbestandsreduktion fuer fiktive Bundle-SKUs
- keine Dolibarr-Komponentenuebergabe fuer Sets

## Spaetere Option

Falls spaeter echte Bundles notwendig werden, kann M2/M3 ein eigenes Bundle-Modell nachziehen:

| Feld | Typ | Zweck |
| --- | --- | --- |
| `bundle_sku` | string | eigene Verkaufs-SKU fuer echtes Bundle |
| `component_sku` | string | enthaltene Komponente |
| `quantity` | decimal | Menge pro Bundle |
| `stock_policy` | enum | Bestand reduzieren oder manuell pruefen |

Diese Option wird bewusst verschoben und nicht fuer M1 umgesetzt.

## Entscheidungsvorlage

Bitte bestaetigen oder anpassen:

- [x] In M1 werden keine technischen Bundles angelegt.
- [x] Es wird keine eigene Bundle-SKU fuer Sets erzeugt.
- [x] Kunden kaufen die betroffenen Artikel als einzelne Produkte.
- [x] Preisvorteile werden ueber Gutschein, Rabatt oder manuelle Preisaktion abgebildet.
- [x] Bestand bleibt auf Einzelprodukt-/Variantenebene.
- [x] Es wird vorerst kein Bundle-Plugin genutzt.
- [x] Eigene Bundle-/Komponentenlogik wird bewusst auf spaeter verschoben.

## Pruefpunkte beim Etsy-Test

- [ ] Gibt es Etsy-Listings, die heute als Set verkauft werden?
- [ ] Koennen diese Sets fachlich als Einzelprodukte plus Rabatt abgebildet werden?
- [ ] Gibt es Etsy-Rabatte/Gutscheine, die uebernommen oder nachgebaut werden muessen?
- [ ] Gibt es einen Fall, bei dem ein echtes Bundle zwingend noetig waere?

## Offene Fragen

- Soll es feste Gutschein-Codes fuer bestimmte Produktkombinationen geben?
- Soll der Rabatt automatisch greifen oder manuell ueber Gutschein?
- Muss ein Rabatt auch in Etsy sichtbar sein oder reicht WooCommerce fuer den Start?

## Naechster Schritt

Nach Entscheidung:

1. Import-Preview behandelt Set-/Bundle-Kandidaten als normale Einzelprodukte.
2. Falls Etsy spaeter echte Bundle-Listings liefert, werden sie mit `needs_review` markiert.
3. Preis-/Rabattlogik wird in M2-040 entschieden.
