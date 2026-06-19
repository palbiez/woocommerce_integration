# WooCommerce-Etsy Integration

Eigene Integrationsloesung fuer den Abgleich zwischen WooCommerce und Etsy.

WooCommerce soll das fuehrende System werden. Etsy wird als Vertriebskanal angebunden. Die Integration soll Produkte, Varianten, SKUs, Bestellungen, Bestand und Versand-/Trackingdaten kontrolliert synchronisieren.

Der aktuelle Projektstand ist Planungs- und Grundlagendokumentation. Produktiver Code fuer die Integrationsapp wird in den naechsten Phasen ergaenzt.

## Zielbild

- Etsy-Listings initial nach WooCommerce importieren
- WooCommerce als fuehrendes System fuer Produktdaten, Preise und Bestand verwenden
- Etsy-Listings aus WooCommerce aktualisieren
- Etsy-Bestellungen nach WooCommerce importieren
- Bestand und Versand-/Trackingdaten zwischen WooCommerce und Etsy synchronisieren
- n8n spaeter fuer Randprozesse wie Benachrichtigungen, Reports und manuelle Freigaben einsetzen
- Dolibarr spaeter ueber REST API anbinden

Der detaillierte Plan steht in [INTEGRATIONSPLAN.md](INTEGRATIONSPLAN.md).

## Lokales Setup

Voraussetzungen fuer lokale Entwicklung:

- Git
- Python 3.13 oder Python 3.10
- PowerShell unter Windows oder eine Bash-kompatible Shell unter Linux/macOS

Auf dem aktuellen Windows-System liegen Python-Installationen typischerweise unter:

- `C:\Users\philipp.albiez\AppData\Local\Programs\Python\Python313`
- `C:\Users\philipp.albiez\AppData\Local\Programs\Python\Python310`

Beispiel fuer ein lokales Python-Environment unter Windows:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Sobald die Python-App ergaenzt ist, werden die konkreten Abhaengigkeiten hier dokumentiert, z. B. `pip install -r requirements.txt`.

## Projektstruktur

```text
.
|-- INTEGRATIONSPLAN.md
|-- anforderungen.md
|-- docs/
|   |-- github-tracking.md
|   |-- reverse-proxy-tls.md
|   `-- secrets.md
`-- scripts/
    |-- setup-github-tracking.ps1
    `-- setup-reverse-proxy-tls.sh
```

## Server- und Deployment-Annahmen

Start ohne Docker:

- Hetzner Linux Server
- Python-App in `/mnt/wci`
- Service-User `etsy_integration`
- Python venv im App-Verzeichnis
- Betrieb als systemd Service
- App bindet nur lokal, z. B. `127.0.0.1:8000`
- Nginx stellt Reverse Proxy und TLS bereit
- n8n wird spaeter separat betrieben, vorzugsweise unter eigener Subdomain

Der Reverse-Proxy- und TLS-Ansatz ist in [docs/reverse-proxy-tls.md](docs/reverse-proxy-tls.md) dokumentiert. Das passende Setup-Script liegt unter [scripts/setup-reverse-proxy-tls.sh](scripts/setup-reverse-proxy-tls.sh).

## Secrets

Produktive Zugangsdaten, API-Keys, Passwoerter und SSH-Schluessel duerfen nicht in Git committed werden.

Der Umgang mit lokalen und produktiven Secrets ist in [docs/secrets.md](docs/secrets.md) dokumentiert.

## GitHub Tracking

Labels, Milestones und Issue-Struktur sind in [docs/github-tracking.md](docs/github-tracking.md) beschrieben. Das Setup-Script fuer die GitHub-Projektstruktur liegt unter [scripts/setup-github-tracking.ps1](scripts/setup-github-tracking.ps1).
