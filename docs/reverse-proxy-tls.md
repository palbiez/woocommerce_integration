# Reverse Proxy und TLS

Stand: 19.06.2026

## Entscheidungsvorschlag

Fuer den Start sollte die Integrationsapp ohne Docker lokal als systemd Service laufen und nur auf `127.0.0.1` binden, z. B. `127.0.0.1:8000`. Oeffentlich erreichbar wird sie ausschliesslich ueber Nginx als Reverse Proxy mit Let's-Encrypt-Zertifikat.

Das passt zum aktuellen Betriebsmodell aus Issue #2:

- kein Docker als Startvoraussetzung
- Service-User `etsy_integration`
- App-Verzeichnis `/mnt/wci`
- bestehender Hetzner-Server mit weiteren Diensten, insbesondere Dolibarr
- n8n spaeter als separater Dienst hinter eigenem Hostnamen oder Pfad

## Empfohlenes Zielbild

```text
Internet
  |
  | https://integration.example.com
  v
Nginx :443
  |
  | http://127.0.0.1:8000
  v
systemd Service: wci-api.service
  |
  v
Python App in /mnt/wci
```

Die Python-App sollte nicht direkt an `0.0.0.0` gebunden werden. Der oeffentliche Zugriff, TLS, HSTS, Weiterleitung von HTTP auf HTTPS und Proxy-Header liegen bei Nginx.

## Voraussetzungen

- Debian/Ubuntu Server mit `apt`
- Domain/Subdomain zeigt per DNS A/AAAA Record auf den Hetzner-Server
- Ports `80/tcp` und `443/tcp` sind in Firewall und Hetzner-Firewall offen
- App laeuft lokal, z. B. `http://127.0.0.1:8000`
- kein anderer Nginx Server-Block verwendet denselben `server_name`

## Setup-Script

Das Script [`scripts/setup-reverse-proxy-tls.sh`](../scripts/setup-reverse-proxy-tls.sh) richtet Nginx, Certbot und den Server-Block ein.

Beispiel auf dem Server aus dem Repository-Verzeichnis:

```bash
sudo bash scripts/setup-reverse-proxy-tls.sh \
  --domain integration.example.com \
  --email admin@example.com \
  --upstream 127.0.0.1:8000 \
  --site-name wci
```

Vor dem produktiven Zertifikat kann mit Let's-Encrypt-Staging getestet werden:

```bash
sudo bash scripts/setup-reverse-proxy-tls.sh \
  --domain integration.example.com \
  --email admin@example.com \
  --upstream 127.0.0.1:8000 \
  --site-name wci \
  --staging
```

Wichtig: Nach einem Staging-Test muss das Staging-Zertifikat fuer den produktiven Betrieb durch ein echtes Zertifikat ersetzt werden. Fuer den finalen Lauf `--staging` weglassen.

## App-Anforderungen

Die App bzw. der ASGI-Server sollte hinter dem Proxy passende Forwarded-Header akzeptieren. Fuer Uvicorn ist typischerweise sinnvoll:

```bash
uvicorn app.main:app \
  --host 127.0.0.1 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips 127.0.0.1
```

Wenn spaeter Webhooks von WooCommerce, Etsy oder n8n eingehen, muessen die externen Webhook-URLs immer die HTTPS-URL verwenden, nicht den lokalen Upstream.

## n8n

n8n sollte nicht in denselben Server-Block gemischt werden. Empfohlen ist eine eigene Subdomain, z. B.:

```text
n8n.example.com -> 127.0.0.1:5678
```

Dafuer kann dasselbe Script erneut mit anderem `--domain`, `--upstream` und `--site-name` ausgefuehrt werden:

```bash
sudo bash scripts/setup-reverse-proxy-tls.sh \
  --domain n8n.example.com \
  --email admin@example.com \
  --upstream 127.0.0.1:5678 \
  --site-name n8n
```

Fuer n8n sollten zusaetzlich die n8n-Umgebungsvariablen passend zur externen URL gesetzt werden, insbesondere `N8N_HOST`, `N8N_PROTOCOL=https` und `WEBHOOK_URL=https://n8n.example.com/`.

## Spaetere Docker-Migration

Bei einer spaeteren Docker-Migration bleibt Nginx als Host-Reverse-Proxy verwendbar. Nur der Upstream aendert sich dann, z. B. auf einen lokal gebundenen Container-Port:

```text
Nginx :443 -> 127.0.0.1:18000 -> App-Container
```

Alternativ kann dann auf einen Docker-nativen Proxy wie Traefik oder Caddy migriert werden. Fuer den aktuellen Start ist Nginx + Certbot risikoarm, weil es gut zu bestehenden nicht-containerisierten Diensten auf dem Server passt.
