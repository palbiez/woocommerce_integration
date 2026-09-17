# Python-Skripte fuer M1

Stand: 19.06.2026

Diese Skripte unterstuetzen Milestone `M1 Etsy Bestandsaufnahme und WooCommerce Migration`.

## Vorbereitung auf Ubuntu

Im Projektverzeichnis auf dem Server:

```bash
cd /mnt/wci/woocommerce_integration
bash scripts/setup-python-venv.sh
source .venv/bin/activate
```

Pruefen:

```bash
which python
python --version
```

Erwartet ist ein Python aus dem Projekt, z. B.:

```text
/mnt/wci/woocommerce_integration/.venv/bin/python
Python 3.13.x
```

Alle Skripte lesen standardmaessig `config.cfg` aus dem Projektverzeichnis. Alternative:

```bash
python scripts/py/wc_api_check.py --config /mnt/wci/woocommerce_integration/config.cfg
```

## Reihenfolge

### M1-010 WooCommerce REST API Zugriff testen

Zuerst pruefen, welche Config und URL Python wirklich nutzt:

```bash
python scripts/py/wc_api_check.py --show-config
```

Danach API-Test ausfuehren:

```bash
python scripts/py/wc_api_check.py
```

Erzeugt einen Bericht unter `data/m1_woocommerce_check/`.

### M1-020 Etsy OAuth und Token-Speicherung als POC bauen

Das Script oeffnet auf dem Server keinen Browser. Es gibt eine OAuth-URL aus und wartet auf die manuelle Rueckgabe aus deinem lokalen Browser:

```bash
python scripts/py/etsy_oauth.py
```

Ablauf:

1. Das Script gibt eine Etsy-OAuth-URL aus.
2. Diese URL lokal im Browser oeffnen.
3. Nach der Freigabe die komplette Redirect-URL oder den `code`-Parameter im Terminal einfuegen.
4. Das Token wird unter `.secrets/etsy_token.json` gespeichert.

Pruefen, ob der Token-Ordner beschreibbar ist:

```bash
mkdir -p .secrets
test -w .secrets && echo "OK: .secrets ist beschreibbar"
```

Falls die Etsy-App eine bestimmte Redirect-URI verlangt:

```bash
python scripts/py/etsy_oauth.py --redirect-uri https://example.com/callback
```

Der lokale Callback-Flow ist nur sinnvoll, wenn ein SSH-Portforwarding eingerichtet ist. Dann explizit starten:

```bash
python scripts/py/etsy_oauth.py --callback
```

### M1-030 Bestehende Etsy Listings analysieren

```bash
python scripts/py/etsy_analyze_listings.py
```

Erzeugt JSON- und CSV-Auswertungen unter `data/m1_etsy_analysis/`. Die Analyse markiert unter anderem fehlende SKUs, Varianten, personalisierte Produkte, Made-to-Order-Kandidaten und Bundle-Kandidaten.

### M1-040 bis M1-070 Decision-Templates erstellen

```bash
python scripts/py/create_m1_decision_templates.py
```

Erzeugt Markdown-Vorlagen unter `docs/m1-decisions/` fuer:

- SKU- und Produktdatenmodell
- Personalisierungsfelder
- Bundle-Modell
- Made-to-Order

### M1-080 Import-Preview Etsy nach WooCommerce erstellen

```bash
python scripts/py/build_import_preview.py
```

Erzeugt `data/m1_import_preview/latest.json`. Dieses Skript schreibt nicht nach WooCommerce.

### M1-090 Initialen WooCommerce Produktimport durchfuehren

Erst Dry-Run:

```bash
python scripts/py/import_preview_to_woocommerce.py
```

Echter Import nur explizit:

```bash
python scripts/py/import_preview_to_woocommerce.py --apply
```

Wenn die Preview fehlende SKUs enthaelt, bricht der Import ab. Das kann nur bewusst uebersteuert werden:

```bash
python scripts/py/import_preview_to_woocommerce.py --apply --allow-missing-sku
```

## Schutzmechanismen

- Zugangsdaten werden aus `config.cfg` gelesen, nicht im Code gespeichert.
- Etsy Tokens liegen unter `.secrets/`.
- API-Ergebnisse, Analysen und Import-Previews liegen unter `data/`.
- Der WooCommerce-Import schreibt erst mit `--apply`.
- Ein erneuter `--apply`-Lauf erkennt bereits importierte Listings ueber `_etsy_listing_id` und aktualisiert Produkt/Varianten statt Duplikate anzulegen.
- Variable Produkte erhalten aus den Etsy-Varianten aggregierte WooCommerce-Attribute; Varianten werden ueber SKU wiedererkannt.
- Ein leerer WooCommerce-Bestand gilt als erfolgreicher API-Read, nicht als fehlgeschlagener Check.

## Kleiner Server-Service auf Port 6001

Der Dienst `scripts/py/etsy_service.py` laeuft auf dem Hetzner-Server als systemd-Service `woocommerce-etsy.service` und bindet nur an `127.0.0.1:6001`.

Routen:

- `GET /healthz` – lokaler Healthcheck
- `GET /oauth/etsy/start` – startet PKCE-OAuth mit Lese- und Schreibrecht fuer Listings und leitet zu Etsy weiter
- `GET /oauth/etsy/callback` – validiert `state`, speichert Token und erstellt den Etsy-Snapshot
- `POST /webhooks/etsy` – speichert eingehende Test-/Webhook-Payloads unter `data/etsy_webhooks/`
- `GET /api/etsy/snapshot` – liest den letzten Snapshot lokal aus

Nach erfolgreicher OAuth-Freigabe wird `data/m1_etsy_snapshot/latest.json` mit Shop-ID, aktiven Listings, Inventory/Varianten und Bildern geschrieben. Die Snapshot-Datei und OAuth-Secrets bleiben durch `.gitignore` ausserhalb von Git.

## SKU-Anreicherung der Etsy-Daten

Einfache WooCommerce-Produkte koennen technisch ohne SKU existieren. Fuer eine stabile Etsy/WooCommerce-Zuordnung werden jedoch alle verkaufbaren Bobbel-Einheiten mit einer eindeutigen SKU versehen. Varianten behalten jeweils eine eigene SKU. Nicht-Bobbel-Produkte wie Garnschalen erhalten spaeter eine eigene Produktgruppen-Syntax.

Verbindliche Syntax:

```text
<Name- oder Nummerncode>-<Lauflänge in Metern>-<Verlaufsart>[-<Duplikatnummer>]
```

Beispiele und Codes:

- `GOLDMARIE` -> `GM`, `BLUE LEMONADE` -> `BL`, `EINZELSTÜCK` -> `ES`
- weitere Namen erhalten zwei stabile Grossbuchstaben, z. B. `WEINLAUB` -> `WL`
- namenlose Bobbel erhalten eine laufende zweistellige Nummer `01` bis `99`
- `NV` normaler Verlauf, `SV` sanfter Verlauf, `VV` verrückter Verlauf, `GV` gemischter Verlauf, `TV` Tuchverlauf
- bei einer echten Kollision wird `-2`, `-3` usw. angehaengt
- Garnschalen verwenden als eigene Produktgruppe `GS-[Größe in cm]`, z. B. `GS-27`

Der Plan wird mit `python3 scripts/py/etsy_update_skus.py` nur angezeigt. Erst `--apply` schreibt die eindeutig ableitbaren Bobbel-SKUs nach Etsy. Vor `--apply` muessen die Vorschlaege fachlich geprueft werden.

Am 17.09.2026 wurden 31 fehlende bzw. kollidierende Bobbel-SKUs nach Etsy geschrieben. Die drei Garnschalen werden separat als `GS-[Größe in cm]` gepflegt.

## Aktueller Ausfuehrungsstatus

- WooCommerce REST API: erreichbar; am 16.09.2026 wurden Produkte, Varianten-/Bestandsfelder und Bestellungen erfolgreich gelesen. Der Shop war dabei leer.
- Etsy Seller App Credentials: am 16.09.2026 mit den aktuellen Werten geprueft; der oeffentliche Etsy-Endpoint antwortete mit HTTP 200. `application/users/me` antwortete ohne OAuth erwartungsgemaess mit HTTP 401 (`shops_r` erforderlich).
- Etsy OAuth: Flow ist implementiert, aber die einmalige Browserfreigabe und Token-Ablage unter `.secrets/etsy_token.json` muss interaktiv durchgefuehrt werden.
- Der echte Etsy-Analyse-/Importlauf und ein produktiver Schreiblauf werden erst nach dieser OAuth-Freigabe und einer fachlichen SKU-Pruefung ausgefuehrt.

## API-Referenzen

- Etsy Open API v3 Authentication: https://developer.etsy.com/documentation/essentials/authentication
- Etsy Open API v3 Reference: https://developers.etsy.com/documentation/reference
- WooCommerce REST API: https://developer.woocommerce.com/docs/apis/rest-api/
