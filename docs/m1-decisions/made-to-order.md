# M1-070 Made-to-Order Bestand und Lieferzeit

Status: entschieden

## Entscheidung

Wie werden Made-to-Order-Produkte bestandsseitig und im Lieferzeitmodell behandelt?

Entscheidung: **Made-to-Order wird in M1 bewusst einfach behandelt. Es gibt normale Produkte bzw. Varianten mit Bestandspuffer. Die laengere Produktionszeit wird ueber ein abweichendes Versandprofil abgebildet. Zusaetzliche Felder wie `production_group`, `availability_policy` oder ein eigener Produktionsstatus werden fuer den Start nicht umgesetzt.**

## Rahmenbedingung

Etsy erlaubt aktuell keinen verlaesslichen Zugriff auf echte Listing-/Inventory-Daten. Deshalb werden einzelne Etsy-Produkte erst beim ersten erfolgreichen Etsy-Test bzw. in der Import-Preview als Made-to-Order erkannt oder markiert.

Konsequenz:

- keine komplexen Made-to-Order-Felder jetzt anlegen
- keine Produktionsgruppen pflegen
- keine eigene Verfuegbarkeitslogik in M1 bauen
- keine automatische Produktionsstatuslogik fuer Bestellungen in M1
- Made-to-Order-Dauer steckt im Versandprofil bzw. in der dort sichtbaren Lieferzeit

## Zielmodell fuer M1

### Produkte

Regel:

```text
Made-to-Order-Produkte bleiben normale WooCommerce-Produkte oder Varianten.
```

Pflicht:

- SKU bleibt die normale Produkt- oder Varianten-SKU.
- Es wird keine neue SKU pro Auftrag erzeugt.
- Produkte koennen bei Bedarf als Made-to-Order markiert oder ueber ihr abweichendes Versandprofil erkannt werden.

### Versandzeit

Regel:

```text
Made-to-Order-Days sind in der Versand-/Lieferzeit enthalten.
```

Umsetzung:

- Standardprodukte nutzen das normale Versandprofil.
- Made-to-Order-Produkte nutzen ein abweichendes Versandprofil mit laengerer Bearbeitungs-/Lieferzeit.
- Es wird in M1 kein separates Feld `made_to_order_days` zwingend gepflegt.

### Bestand

Regel:

```text
Made-to-Order-Produkte koennen mit einem Bestandspuffer gefuehrt werden.
```

Beispiel:

```text
Bestand: 10
Bestellung geht ein: Bestand 9
Nach Versand/Fertigstellung: Bestand wieder auf 10 setzen
```

Pflicht:

- Bestand ist ein Verkaufs-/Kapazitaetspuffer, kein exakter physischer Lagerbestand.
- Der Bestandspuffer wird bewusst klein genug gewaehlt, um Ueberverkauf zu vermeiden.
- Fuer M1 reicht manuelles oder spaeter einfach automatisiertes Zuruecksetzen nach Versand.

## Nicht-Ziele in M1

- kein Feld `production_group`
- keine komplexe `availability_policy`
- kein eigener Produktionsstatus je Bestellung
- keine getrennte Rechnung `Produktionszeit + Versandzeit`
- keine automatische Kapazitaetsplanung
- keine Komponentenlogik fuer Made-to-Order-Produkte

## Entscheidungsvorlage

Bitte bestaetigen oder anpassen:

- [x] Made-to-Order aendert die SKU nicht.
- [x] Made-to-Order-Produkte bleiben normale Produkte oder Varianten.
- [x] Die laengere Made-to-Order-Zeit wird ueber ein abweichendes Versandprofil abgebildet.
- [x] `made_to_order_days` ist in M1 kein Pflichtfeld, weil die Tage in der Versandzeit stecken.
- [x] `production_group` wird in M1 nicht genutzt.
- [x] `availability_policy` wird in M1 nicht genutzt.
- [x] Bestand kann als Puffer gefuehrt werden, z. B. 10, und nach Versand wieder erhoeht werden.
- [x] Produktionsstatus fuer Bestellungen wird in M1 nicht umgesetzt.

## Pruefpunkte beim Etsy-Test

- [ ] Welche Etsy-Listings nutzen ein abweichendes Versandprofil?
- [ ] Welche Listings sind dadurch Made-to-Order?
- [ ] Welche Standard-Bestandspuffer sind sinnvoll, z. B. 5 oder 10?
- [ ] Muss der Bestand nach Versand manuell oder automatisch wieder aufgefuellt werden?
- [ ] Gibt es einzelne Produkte, bei denen der Bestandspuffer nicht reicht und echte Materialknappheit relevant ist?

## Offene Fragen

- Soll der Bestandspuffer einheitlich sein oder je Produkt variieren?
- Soll das Zuruecksetzen des Bestands nach Versand spaeter automatisiert werden?
- Soll WooCommerce Made-to-Order-Produkte sichtbar kennzeichnen oder reicht das Versandprofil?

## Naechster Schritt

Nach Entscheidung:

1. Beim ersten Etsy-Test Versandprofile auswerten.
2. Made-to-Order-Produkte ueber abweichendes Versandprofil markieren.
3. Import-Preview um Versandprofil und empfohlenen Bestandspuffer ergaenzen.
