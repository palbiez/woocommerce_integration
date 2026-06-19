# Python-Skripte fuer M1

Stand: 19.06.2026

Diese Skripte unterstuetzen Milestone `M1 Etsy Bestandsaufnahme und WooCommerce Migration`.

## Vorbereitung

Unter Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-python-venv.ps1
.\.venv\Scripts\Activate.ps1
```

Unter Linux/macOS:

```bash
bash scripts/setup-python-venv.sh
source .venv/bin/activate
```

Alle Skripte lesen standardmaessig `config.cfg` aus dem Projektverzeichnis. Alternative:

```powershell
python .\scripts\py\wc_api_check.py --config C:\pfad\zu\config.cfg
```

## Reihenfolge

### M1-010 WooCommerce REST API Zugriff testen

```powershell
python .\scripts\py\wc_api_check.py
```

Erzeugt einen Bericht unter `data/m1_woocommerce_check/`.

### M1-020 Etsy OAuth und Token-Speicherung als POC bauen

```powershell
python .\scripts\py\etsy_oauth.py
```

Das Token wird unter `.secrets/etsy_token.json` gespeichert. Dieser Pfad ist in `.gitignore` eingetragen.

Falls der lokale Callback nicht zur Etsy-App passt, kann die Redirect-URI explizit gesetzt und die Rueckgabe manuell eingefuegt werden:

```powershell
python .\scripts\py\etsy_oauth.py --redirect-uri https://example.com/callback --manual
```

### M1-030 Bestehende Etsy Listings analysieren

```powershell
python .\scripts\py\etsy_analyze_listings.py
```

Erzeugt JSON- und CSV-Auswertungen unter `data/m1_etsy_analysis/`. Die Analyse markiert unter anderem fehlende SKUs, Varianten, personalisierte Produkte, Made-to-Order-Kandidaten und Bundle-Kandidaten.

### M1-040 bis M1-070 Decision-Templates erstellen

```powershell
python .\scripts\py\create_m1_decision_templates.py
```

Erzeugt Markdown-Vorlagen unter `docs/m1-decisions/` fuer:

- SKU- und Produktdatenmodell
- Personalisierungsfelder
- Bundle-Modell
- Made-to-Order

### M1-080 Import-Preview Etsy nach WooCommerce erstellen

```powershell
python .\scripts\py\build_import_preview.py
```

Erzeugt `data/m1_import_preview/latest.json`. Dieses Skript schreibt nicht nach WooCommerce.

### M1-090 Initialen WooCommerce Produktimport durchfuehren

Erst Dry-Run:

```powershell
python .\scripts\py\import_preview_to_woocommerce.py
```

Echter Import nur explizit:

```powershell
python .\scripts\py\import_preview_to_woocommerce.py --apply
```

Wenn die Preview fehlende SKUs enthaelt, bricht der Import ab. Das kann nur bewusst uebersteuert werden:

```powershell
python .\scripts\py\import_preview_to_woocommerce.py --apply --allow-missing-sku
```

## Schutzmechanismen

- Zugangsdaten werden aus `config.cfg` gelesen, nicht im Code gespeichert.
- Etsy Tokens liegen unter `.secrets/`.
- API-Ergebnisse, Analysen und Import-Previews liegen unter `data/`.
- Der WooCommerce-Import schreibt erst mit `--apply`.

## API-Referenzen

- Etsy Open API v3 Authentication: https://developer.etsy.com/documentation/essentials/authentication
- Etsy Open API v3 Reference: https://developers.etsy.com/documentation/reference
- WooCommerce REST API: https://developer.woocommerce.com/docs/apis/rest-api/
