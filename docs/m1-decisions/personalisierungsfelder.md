# M1-050 WooCommerce Erweiterung fuer Personalisierungsfelder

Status: entschieden fuer M1, technische Plugin-Pruefung vor Produktivbetrieb erforderlich

## Entscheidung

Fuer den Start wird `Extra Product Options For WooCommerce | Custom Product Addons and Fields` von ThemeHigh als kostenlose Loesung fuer kundennahe Produktfelder eingesetzt. Interne Produkt-/Produktionsdaten werden als WooCommerce-Metadaten bzw. Custom Fields gepflegt. Die Integrationsschicht normalisiert Add-on-Werte aus den Bestellpositions-Metadaten und bleibt unabhaengig vom Plugin-Feldnamen.

Welche WooCommerce-Erweiterung oder Eigenlogik bildet personalisierte Produktfelder ab?

Ziel: Kunden sollen notwendige Personalisierungsdaten im Shop sauber erfassen koennen. Diese Daten muessen in der Bestellung sichtbar sein und spaeter fuer Produktion, Etsy-Sync und optional Dolibarr auslesbar bleiben.

## Rahmenbedingung

Es soll kein Geld investiert werden. Der Shop ist leer und es gibt kaum bestehendes WooCommerce-Customizing.

Konsequenz:

- keine kostenpflichtige WooCommerce-Erweiterung als Startvoraussetzung
- kein komplexer Eigenbau im Checkout
- kostenlose Plugin-Loesung bevorzugen
- erst testen, dann produktiv festlegen

## Empfehlung

Empfohlener Startansatz: **kostenloses Plugin `Extra Product Options For WooCommerce | Custom Product Addons and Fields` von ThemeHigh verwenden, plus eigene Normalisierung in der Integration.**

Begruendung:

- Passt zum aktuellen Umfang von ca. 25 bis 100 Produkten.
- Ist kostenlos aus dem WordPress-Pluginverzeichnis installierbar.
- Bietet in der freien Version typische Eingabetypen wie Text, Textarea, Select, Radio, Checkbox, Date Picker, Color Picker und weitere Felder.
- Unterstuetzt Pflichtfelder und Display Rules.
- Zeigt Feldwerte laut Plugin-Doku in Cart, Checkout, Thank-you Page, My Account, WooCommerce Orders, E-Mails und PDF/Invoice-Plugins an.
- Passt gut, weil der Shop leer ist und kein bestehendes Customizing migriert werden muss.
- Reduziert Eigenentwicklung im Checkout, der besonders fehleranfaellig ist.

Wichtige Einschraenkung:

- Das Plugin ist nicht fuer SKU-, Bestands- oder Bundle-Komponentenlogik zustaendig.
- Preisaufschlaege, komplexe Validierung und einige erweiterte Feldtypen koennen je nach Plugin in Pro-Versionen liegen.
- API-Auslesbarkeit muss im Shop konkret getestet werden, bevor die Entscheidung final geschlossen wird.

Deshalb: kostenloses Extra-Product-Options-Plugin fuer Kundeneingaben nutzen, aber Bestands-/SKU-/Bundle-Logik strikt in der eigenen Integration modellieren.

## Bewertungsmatrix

| Kriterium | Gewicht | ThemeHigh Extra Product Options Free | PPOM Free | ACF/Custom Fields | Eigene Checkout-Logik |
| --- | ---: | --- | --- | --- |
| Checkout-Darstellung ohne Eigenentwicklung | hoch | stark | stark | schwach bis mittel | mittel |
| Pflichtfelder und einfache Validierung | hoch | stark | stark | braucht Zusatzlogik | stark, aber Eigenaufwand |
| Anzeige in Bestellung | hoch | stark laut Plugin-Doku | wahrscheinlich stark | braucht Zusatzlogik | stark, wenn sauber gebaut |
| API-/Exportfaehigkeit | hoch | muss getestet werden | muss getestet werden | mittel | stark, wenn sauber gebaut |
| Wartbarkeit | hoch | stark | mittel | mittel | schwach bis mittel |
| Risiko im Checkout | hoch | niedrig | niedrig bis mittel | mittel | hoch |
| Kosten | hoch | kostenlos | kostenlos | kostenlos/optional Pro | Entwicklungszeit |
| Datei-Upload kostenlos | mittel | unklar/nicht als Standard annehmen | laut Plugin-Beschreibung vorhanden | nein | ja, aber Eigenaufwand |
| Geeignet fuer SKU/Bestand | hoch | nein | nein | nein | nur mit eigener Logik |

## Kandidat 1: Extra Product Options For WooCommerce von ThemeHigh

Beschreibung:

Kostenloses WordPress-Plugin fuer WooCommerce-Produktfelder. Die freie Version bietet laut Pluginseite bis zu 20 Feldtypen, u. a. Text, Textarea, Select, Radio Button, Checkbox, Date Picker, Color Picker, Time Picker und weitere Felder. Es unterstuetzt Custom Sections, Display Rules und Pflichtfelder.

Staerken:

- kostenlos
- fuer leeren Shop gut geeignet
- viele freie Feldtypen
- Pflichtfelder moeglich
- Display Rules moeglich
- Feldwerte werden laut Plugin-Doku in Cart, Checkout, Thank-you Page, My Account, WooCommerce Orders und E-Mails angezeigt
- geringe Einstiegskosten und wenig Eigenentwicklung

Schwaechen:

- erweiterte Features werden als Premium beworben
- Preisfelder, fortgeschrittene Validierung und weitere Feldtypen koennen Pro-Funktionen sein
- API-Auslesbarkeit der Bestellpositionsdaten muss getestet werden
- nicht fuer SKU, Bestand oder Bundle-Komponenten geeignet

Geeignet fuer:

- Namenspersonalisierung
- Freitext
- Auswahl aus festen Optionen
- Geschenknotizen
- einfache Produktionshinweise ohne Preisaufschlag

Nicht geeignet fuer:

- Bundle-Komponentenbestand
- Varianten-SKU-Logik
- komplexe Produktkonfiguration mit vielen abhaengigen Regeln
- Preisaufschlaege ohne Pruefung der Free-Version

Bewertung:

```text
Empfohlen fuer Start, weil kostenlos, passend fuer leeren Shop und ausreichend fuer einfache Personalisierung.
```

## Kandidat 2: PPOM Free

Beschreibung:

Kostenloses WordPress-Plugin fuer personalisierte Produktoptionen. Die Pluginbeschreibung nennt Text Inputs, Dropdowns, Checkboxes, Radio Buttons, Date Picker, File Uploads und weitere Felder.

Staerken:

- kostenlos
- laut Pluginbeschreibung Datei-Uploads moeglich
- geeignet, wenn Uploads fuer personalisierte Produkte zwingend benoetigt werden
- direkte Produktseitenfelder ohne Eigenentwicklung

Schwaechen:

- vor Entscheidung muss konkret getestet werden, wie die Daten in WooCommerce Orders und REST API erscheinen
- moegliche Free/Pro-Grenzen im Detail pruefen
- nicht fuer SKU, Bestand oder Bundle-Komponenten geeignet

Bewertung:

```text
Alternative, wenn Datei-Uploads schon in M1 sicher benoetigt werden.
```

## Kandidat 3: ACF oder normale Custom Fields

Beschreibung:

ACF bzw. Custom Fields sind gut fuer interne Produkt-Metadaten, z. B. Produktionszeit, Materialhinweise, interne Kategorien oder Sync-Steuerung.

Staerken:

- Gut fuer interne Felder am Produkt.
- Flexibel fuer Admin-Pflege.
- Sinnvoll fuer technische Metadaten wie `made_to_order_days`, `production_group`, `sync_exclude`.

Schwaechen:

- Nicht automatisch eine saubere Kunden-Eingabe im Checkout.
- Fuer Pflichtfelder im Warenkorb/Checkout braucht es Zusatzlogik.
- Risiko, dass Shop-Anzeige, Checkout, Order-Meta und API auseinanderlaufen.

Geeignet fuer:

- interne Produktdaten
- Sync-Steuerung
- Produktions-/Lieferzeitlogik
- Mapping-Hilfsfelder

Nicht geeignet als alleiniger Ansatz fuer:

- Kundeneingaben auf Produktseite
- validierte Pflichtfelder im Checkout

Bewertung:

```text
Als kostenlose Ergaenzung sinnvoll, aber nicht als alleinige Loesung fuer Personalisierung im Checkout.
```

## Kandidat 4: Eigene Checkout-/Produktfeld-Logik

Beschreibung:

Eigene WordPress/WooCommerce-Erweiterung fuer Produktfelder, Validierung, Order-Line-Meta und API-Ausgabe.

Staerken:

- Maximale Kontrolle.
- Datenformat kann exakt zur Integration passen.
- Gute Basis fuer sehr komplexe Regeln.

Schwaechen:

- Hoechster Entwicklungs- und Testaufwand.
- Checkout-Fehler wirken direkt auf Bestellungen.
- Wartungsaufwand bei WooCommerce-Updates.

Geeignet fuer:

- komplexe Regeln mit Abhaengigkeiten
- Produktkonfigurator
- Sonderfaelle, die kostenlose Plugins nicht sauber abbilden

Bewertung:

```text
Nicht als Startloesung empfohlen. Als spaetere Erweiterung offenhalten.
```

## Empfohlene Zielarchitektur

```text
ThemeHigh Extra Product Options Free
  -> Kundeneingaben an Produkt/Bestellposition
  -> WooCommerce Order Line Item Meta
  -> eigene Integration normalisiert Felder
  -> Produktion / Etsy / Dolibarr

ACF oder Custom Fields
  -> interne Produkt-Metadaten
  -> Made-to-Order, Produktionszeit, Sync-Steuerung
```

## Feldmodell

Vorschlag fuer normalisierte Felddefinitionen in der Integration:

| Feld | Beispiel | Zweck |
| --- | --- | --- |
| `field_key` | `personalization_name` | stabiler technischer Name |
| `label` | `Name` | Anzeige fuer Admin/Produktion |
| `type` | `text` | Feldtyp |
| `required` | `true` | Pflichtfeld |
| `source` | `product_addons` | Herkunft |
| `etsy_equivalent` | `personalization` | spaetere Etsy-Zuordnung |
| `production_export` | `true` | relevant fuer Produktion |

## Entscheidungsoptionen

### Option A: ThemeHigh Extra Product Options Free als Standard, Custom Fields fuer interne Daten

Entscheidung:

```text
ThemeHigh Extra Product Options Free fuer kundennahe Personalisierung.
Custom Fields/ACF fuer interne Produkt- und Produktionsdaten.
Eigene Integration normalisiert alles fuer Sync und Export.
```

Vorteile:

- schnell entscheidbar
- keine Kosten
- geringes Checkout-Risiko
- gute Trennung zwischen Kundeneingabe und interner Steuerung

Nachteile:

- Plugin-Abhaengigkeit von einem kostenlosen Drittanbieter-Plugin
- moegliche Grenzen bei sehr komplexen Konfigurationen
- API-Auslesbarkeit muss getestet werden

Empfehlung:

```text
Ja, als Startentscheidung.
```

### Option B: PPOM Free als Standard

Vorteile:

- kostenlos
- Datei-Uploads laut Pluginbeschreibung moeglich
- gut, wenn Upload-Personalisierung frueh benoetigt wird

Nachteile:

- API- und Order-Meta-Format muss getestet werden
- ebenfalls Plugin-Abhaengigkeit

Empfehlung:

```text
Nur waehlen, wenn Datei-Uploads jetzt schon zwingend sind oder ThemeHigh die noetigen Felder nicht abdeckt.
```

### Option C: Nur Custom Fields/ACF

Vorteile:

- flexibel im Admin
- gut fuer Produkt-Metadaten
- kostenlos moeglich

Nachteile:

- Checkout-/Order-Line-Erfassung muss separat gebaut werden
- hoeheres Risiko fuer Pflichtfeldvalidierung

Empfehlung:

```text
Nicht als alleinige Startentscheidung.
```

### Option D: Vollstaendig eigene Plugin-Logik

Vorteile:

- maximale Kontrolle

Nachteile:

- hoechster Aufwand
- hoechstes Betriebsrisiko
- keine direkten Lizenzkosten, aber Entwicklungszeit

Empfehlung:

```text
Nur wenn kostenlose Plugins fachlich nicht ausreichen.
```

## Entscheidungsvorlage

Bitte bestaetigen oder anpassen:

- [ ] Keine kostenpflichtige Erweiterung wird als Startvoraussetzung genutzt.
- [ ] ThemeHigh Extra Product Options Free wird als erste kostenlose Plugin-Option getestet.
- [ ] PPOM Free wird nur dann bevorzugt, wenn Datei-Uploads sofort benoetigt werden oder ThemeHigh nicht ausreicht.
- [ ] Interne Produktfelder werden ueber Custom Fields/ACF oder eigene Metadaten gepflegt.
- [ ] SKU, Bestand und Bundle-Komponenten werden nicht ueber das Personalisierungsplugin modelliert.
- [ ] Die Integration bekommt eine Normalisierungsschicht fuer Personalisierungsdaten.
- [ ] Komplexe Sonderfaelle werden zuerst dokumentiert, nicht sofort individuell programmiert.

## Pruefpunkte vor Installation/Test

- [ ] Unterstuetzt die kostenlose Version die benoetigten Feldtypen: Text, Textarea, Select, Radio, Checkbox?
- [ ] Falls Datei-Upload benoetigt wird: ist er in der kostenlosen Variante wirklich verfuegbar?
- [ ] Sind Add-on-Werte in Bestellungen und E-Mails sichtbar?
- [ ] Sind Add-on-Werte in der WooCommerce REST API bzw. Order-Daten auslesbar?
- [ ] Funktioniert es mit variablen Produkten ausreichend fuer eure Produktlogik?
- [ ] Sind Pflichtfelder im Checkout verlaesslich validiert?
- [ ] Ist das Plugin mit aktueller WooCommerce-/WordPress-Version kompatibel?
- [ ] Laesst sich das Plugin ohne bestehende Shop-Anpassungen sauber entfernen oder wechseln?

## Offene Fragen

- Welche konkreten Etsy-Personalisierungsfelder existieren heute?
- Brauchen manche Varianten unterschiedliche Personalisierungsfelder?
- Werden Datei-Uploads benoetigt? Wenn ja, sofort oder spaeter?
- Muessen Personalisierungswerte an Dolibarr oder nur an Produktion uebergeben werden?
- Muss Personalisierung den Preis beeinflussen?

## Quellen

- Extra Product Options For WooCommerce von ThemeHigh: https://wordpress.org/plugins/woo-extra-product-options/
- PPOM Product Addons & Custom Fields for WooCommerce: https://wordpress.org/plugins/woocommerce-product-addon/
- Flexible Product Fields: https://wordpress.org/plugins/flexible-product-fields/
- WooCommerce REST API: https://woocommerce.com/document/woocommerce-rest-api/
- ACF Dokumentation: https://www.advancedcustomfields.com/resources/
- WooCommerce Product Custom Fields API: https://developer.woocommerce.com/docs/apis/rest-api/v3/product-custom-fields/
