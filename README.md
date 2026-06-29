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
- Python 3.13
- Bash-kompatible Shell

Auf dem Hetzner-Server liegt die Projekt-venv unter:

- `/mnt/wci/woocommerce_integration/.venv`

Beispiel fuer das Python-Environment unter Ubuntu:

```bash
cd /mnt/wci/woocommerce_integration
bash scripts/setup-python-venv.sh
source .venv/bin/activate
python -m pip install --upgrade pip
```

Sobald die Python-App ergaenzt ist, werden die konkreten Abhaengigkeiten hier dokumentiert, z. B. `pip install -r requirements.txt`.

## Projektstruktur

```text
.
|-- INTEGRATIONSPLAN.md
|-- anforderungen.md
|-- docs/
|   |-- configuration.md
|   |-- github-tracking.md
|   |-- m1-python-scripts.md
|   |-- reverse-proxy-tls.md
|   `-- secrets.md
`-- scripts/
    |-- setup-python-venv.sh
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
- App bindet nur lokal, z. B. `127.0.0.1:6001`
- Nginx stellt Reverse Proxy und TLS auf `8443` bereit
- n8n wird spaeter separat betrieben, vorzugsweise unter eigener Subdomain

Die lokale Konfiguration steht in `config.cfg` im INI-Format. Aufbau und Lese-Beispiele fuer Python und Shell stehen in [docs/configuration.md](docs/configuration.md).

Der Reverse-Proxy- und TLS-Ansatz ist in [docs/reverse-proxy-tls.md](docs/reverse-proxy-tls.md) dokumentiert. Das passende Setup-Script liegt unter [scripts/setup-reverse-proxy-tls.sh](scripts/setup-reverse-proxy-tls.sh).

Die Python-Skripte fuer Milestone M1 sind in [docs/m1-python-scripts.md](docs/m1-python-scripts.md) dokumentiert.

Die persistente Mapping-Datenbank fuer M2 ist in [docs/m2-mapping-db.md](docs/m2-mapping-db.md) dokumentiert. Das Initialisierungsskript liegt unter [scripts/py/m2_mapping_db.py](scripts/py/m2_mapping_db.py).

## Secrets

Produktive Zugangsdaten, API-Keys, Passwoerter und SSH-Schluessel duerfen nicht in Git committed werden.

Der Umgang mit lokalen und produktiven Secrets ist in [docs/secrets.md](docs/secrets.md) dokumentiert.

## GitHub Tracking

Labels, Milestones und Issue-Struktur sind in [docs/github-tracking.md](docs/github-tracking.md) beschrieben. Das Setup-Script fuer die GitHub-Projektstruktur liegt unter [scripts/setup-github-tracking.ps1](scripts/setup-github-tracking.ps1).
