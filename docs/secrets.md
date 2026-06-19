# Secrets und Zugangsdaten

Stand: 19.06.2026

## Grundsatz

Secrets bleiben ausserhalb von Git. Dazu gehoeren insbesondere:

- WooCommerce Consumer Key und Consumer Secret
- WordPress App-Passwoerter
- Etsy Client Secret, OAuth Tokens und Refresh Tokens
- Dolibarr API Keys
- Datenbankpasswoerter
- SSH-Schluessel
- produktive `.env`-Dateien
- lokale `config.cfg`

Die `.gitignore` blockiert bekannte lokale Secret-Dateien bereits, unter anderem `config.cfg`, `hetzner`, `.env` und `.env.*`.

## Lokale Entwicklung

Fuer lokale Entwicklung sollte spaeter eine `.env` oder `.env.local` verwendet werden. Diese Datei wird nicht committed.

Empfohlenes Muster:

```text
WOOCOMMERCE_BASE_URL=https://example.com
WOOCOMMERCE_CONSUMER_KEY=...
WOOCOMMERCE_CONSUMER_SECRET=...
ETSY_CLIENT_ID=...
ETSY_CLIENT_SECRET=...
```

Sobald die App-Konfiguration implementiert ist, sollte eine `.env.example` ohne echte Werte committed werden. Diese Datei zeigt nur die benoetigten Variablennamen.

## Produktiver Server

Fuer den Start ohne Docker ist eine systemd-Environment-Datei sinnvoll:

```text
/etc/wci/wci.env
```

Empfohlene Rechte:

```bash
sudo install -d -o root -g etsy_integration -m 0750 /etc/wci
sudo touch /etc/wci/wci.env
sudo chown root:etsy_integration /etc/wci/wci.env
sudo chmod 0640 /etc/wci/wci.env
```

Der systemd Service kann diese Datei spaeter per `EnvironmentFile=/etc/wci/wci.env` laden. Die Datei liegt damit nicht im Repository und ist nur fuer root und die Service-Gruppe lesbar.

## Rotation

Da produktive Zugangsdaten bereits lokal in Klartextdateien vorliegen, sollten vor produktiver Weiterarbeit rotiert werden:

- WordPress App-Passwort
- WooCommerce API-Key und API-Secret
- Etsy App Secret bzw. OAuth Tokens
- weitere produktive API Keys, falls vorhanden

Nach Rotation sollten alte Tokens in den jeweiligen Systemen deaktiviert werden.

## Umgang mit Backups und Logs

- Backups von Secret-Dateien muessen denselben Schutz wie die Originaldateien haben.
- Logs duerfen keine API Keys, Tokens oder Passwoerter enthalten.
- Fehlermeldungen sollten Secret-Werte maskieren.
- GitHub Issues und Pull Requests duerfen keine echten Zugangsdaten enthalten.
