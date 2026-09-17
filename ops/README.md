# Serverseitige Proxy-Konfiguration

`ops/nginx/etsy-public-endpoints.locations.conf` ist ein Nginx-Konfigurationsfragment fuer den bestehenden TLS-VirtualHost. Es wird innerhalb des bereits vorhandenen `server {}`-Blocks eingebunden; es ist kein zweiter konkurrierender VirtualHost.

Die OAuth-Callback-Route und die Etsy-Webhook-Route bleiben bewusst ohne Authelia-Schutz. Alle anderen bestehenden Routen behalten ihre bisherige Authelia-Regelung. Eine Authelia-Konfigurationsaenderung ist fuer diese beiden oeffentlichen Endpunkte nicht erforderlich.

Vorgeschlagene URLs:

- `https://integration.mrs-daui.de:8443/oauth/etsy/callback`
- `https://integration.mrs-daui.de:8443/webhooks/etsy`

Vor Aktivierung auf dem Server muessen der bestehende Nginx-VirtualHost, Zertifikatspfade, Nginx-Include-Pfad und die Firewall geprueft werden.

Der Nginx-VirtualHost und die systemd-Unit sind auf dem Server als Symlinks aus diesem Projekt aktiviert. Der Dienst lauscht lokal auf `127.0.0.1:6001`; der oeffentliche Zugriff erfolgt nur ueber TLS/Nginx.
