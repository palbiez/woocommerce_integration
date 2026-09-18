# Konfiguration

Stand: 19.06.2026

## Format

Die lokale `config.cfg` verwendet INI-Syntax. Das Format ist bewusst einfach gehalten:

- Sections stehen in eckigen Klammern, z. B. `[AppData_server]`
- Werte werden mit `Key = Value` gesetzt
- Kommentare koennen mit `#` oder `;` beginnen
- Schluessel sind fuer Python `configparser` standardmaessig case-insensitive

Die Datei enthaelt produktive Zugangsdaten und wird nicht committed. Sie ist in `.gitignore` eingetragen.

## Erwartete Sections

```ini
[Wordpress]
Url = https://shop.mrsdaui.de
Username = Integration
AppPassword = ...

[Woocommerce]
Url = https://shop.mrsdaui.de
ApiKey = ...
ApiSecret = ...
WebhookSecret = ...

[EtsyAPI]
AppName = integration-woocommerce
KeyString = ...
Secret = ...
WebhookSecret = ...
ShopId =

[Server]
Ip = 78.47.204.164
Username = root
KeyFile = hetzner

[AppData_server]
Username = etsy_integration
Password = ...
Path = /mnt/wci/woocommerce_integration/
Port = 6001
Domain = integration.mrs-daui.de
ExternalPort = 8443
BindHost = 127.0.0.1
SiteName = wci
CertbotEmail =
CertbotStaging = false
```

Bei einer Etsy **Seller App** sind `KeyString` und `Secret` die App-Zugangsdaten. Jede Etsy-API-Anfrage verwendet daraus den Header `x-api-key: KeyString:Secret`. Seller-/Shopdaten und Schreibzugriffe benoetigen zusaetzlich einen OAuth-2.0-Token mit den erforderlichen Scopes. `ShopId` kann leer bleiben, wenn sie nach OAuth ueber `application/users/me` ermittelt wird.

`Woocommerce.WebhookSecret` bleibt ausserhalb von Git. Der Service prueft damit den Base64-HMAC-SHA256-Wert
aus `X-WC-Webhook-Signature` ueber den unveraenderten Request-Body und behandelt
`X-WC-Webhook-ID` idempotent. Alternativ kann der Secret-Wert als Umgebungsvariable
`WOOCOMMERCE_WEBHOOK_SECRET` gesetzt werden.
Der Service verwendet ersatzweise auch `.secrets/woocommerce_webhook_secret`.

Für Etsy-Webhooks wird das Signing Secret aus dem Etsy Webhook Portal als `EtsyAPI.WebhookSecret`
hinterlegt. Der Service prüft damit den signierten Roh-Body, akzeptiert nur Zeitstempel innerhalb von
fünf Minuten und verarbeitet eine `webhook-id` nur einmal.

## Reverse Proxy

Das Script [`scripts/setup-reverse-proxy-tls.sh`](../scripts/setup-reverse-proxy-tls.sh) liest seine Werte aus `[AppData_server]`.

| Key | Bedeutung |
| --- | --- |
| `Domain` | Externer Hostname, z. B. `integration.mrs-daui.de` |
| `Port` | Lokaler Upstream-Port der App |
| `ExternalPort` | Oeffentlicher HTTPS-Port von Nginx, aktuell `8443` |
| `BindHost` | Lokale Upstream-Adresse, standardmaessig `127.0.0.1` |
| `SiteName` | Name fuer Nginx-Site-Datei und Logs |
| `CertbotEmail` | Optionale E-Mail fuer Let's Encrypt |
| `CertbotStaging` | `true` fuer Staging-Test, sonst `false` |

Mit den aktuellen Werten ergibt sich:

```text
https://integration.mrs-daui.de:8443 -> http://127.0.0.1:6001
```

Das Script akzeptiert keine Setup-Argumente mehr. Der normale Aufruf auf dem Server ist:

```bash
sudo bash scripts/setup-reverse-proxy-tls.sh
```

Falls die Konfigurationsdatei an einem anderen Pfad liegt:

```bash
sudo CONFIG_FILE=/etc/wci/config.cfg bash scripts/setup-reverse-proxy-tls.sh
```

## Lesen in Python

```python
import configparser

config = configparser.ConfigParser()
config.read("config.cfg", encoding="utf-8")

domain = config.get("AppData_server", "Domain")
upstream_port = config.getint("AppData_server", "Port")
external_port = config.getint("AppData_server", "ExternalPort")
```

## Lesen in Shell-Scripts

Bash hat keinen eingebauten INI-Parser. Fuer einfache Scripts sollte eine kleine Parser-Funktion wie im Reverse-Proxy-Script verwendet werden. Dort werden Kommentare, Sections und `Key = Value` sauber behandelt.

Direktes `source config.cfg` ist nicht geeignet, weil INI-Sections keine gueltige Shell-Syntax sind und Secret-Werte Leerzeichen enthalten koennen.
