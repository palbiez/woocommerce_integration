#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  sudo bash scripts/setup-reverse-proxy-tls.sh

Sets up Nginx as TLS reverse proxy for the WooCommerce/Etsy integration app.
All deployment values are read from config.cfg.

Required config values:
  [AppData_server]
  Domain = integration.example.com
  Port = 6001
  ExternalPort = 8443

Optional config values:
  BindHost = 127.0.0.1
  SiteName = wci
  CertbotEmail = admin@example.com
  CertbotStaging = false

Assumptions:
  - Debian/Ubuntu server with apt
  - DNS A/AAAA record for Domain already points to this server
  - Ports 80 and ExternalPort are reachable from the internet
  - The app listens locally on BindHost:Port

Set CONFIG_FILE=/path/to/config.cfg to use a non-default config file.
EOF
}

read_ini_value() {
  local section="$1"
  local key="$2"
  local file="$3"

  awk -v section="$section" -v key="$key" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }

    BEGIN {
      wanted_section = tolower(section)
      wanted_key = tolower(key)
      in_section = 0
    }

    /^[[:space:]]*($|[#;])/ {
      next
    }

    /^[[:space:]]*\[/ {
      line = $0
      sub(/^[[:space:]]*\[/, "", line)
      sub(/\][[:space:]]*$/, "", line)
      in_section = (tolower(trim(line)) == wanted_section)
      next
    }

    in_section {
      line = $0
      sub(/[[:space:]]*[#;].*$/, "", line)
      separator = index(line, "=")
      if (separator == 0) {
        next
      }

      current_key = trim(substr(line, 1, separator - 1))
      current_value = trim(substr(line, separator + 1))

      if (tolower(current_key) == wanted_key) {
        print current_value
        exit
      }
    }
  ' "$file"
}

require_config_value() {
  local name="$1"
  local value="$2"

  if [[ -z "$value" ]]; then
    echo "Missing required config value: $name" >&2
    exit 2
  fi
}

require_port() {
  local name="$1"
  local value="$2"

  if [[ ! "$value" =~ ^[0-9]+$ ]] || (( value < 1 || value > 65535 )); then
    echo "Invalid port in config value $name: $value" >&2
    exit 2
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "This script reads deployment values from config.cfg and does not accept setup arguments." >&2
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${CONFIG_FILE:-${REPO_ROOT}/config.cfg}"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 2
fi

DOMAIN="$(read_ini_value "AppData_server" "Domain" "$CONFIG_FILE")"
UPSTREAM_PORT="$(read_ini_value "AppData_server" "Port" "$CONFIG_FILE")"
EXTERNAL_PORT="$(read_ini_value "AppData_server" "ExternalPort" "$CONFIG_FILE")"
UPSTREAM_HOST="$(read_ini_value "AppData_server" "BindHost" "$CONFIG_FILE")"
SITE_NAME="$(read_ini_value "AppData_server" "SiteName" "$CONFIG_FILE")"
EMAIL="$(read_ini_value "AppData_server" "CertbotEmail" "$CONFIG_FILE")"
CERTBOT_STAGING="$(read_ini_value "AppData_server" "CertbotStaging" "$CONFIG_FILE")"

UPSTREAM_HOST="${UPSTREAM_HOST:-127.0.0.1}"
EXTERNAL_PORT="${EXTERNAL_PORT:-8443}"
SITE_NAME="${SITE_NAME:-wci}"
CERTBOT_STAGING="${CERTBOT_STAGING:-false}"

require_config_value "AppData_server.Domain" "$DOMAIN"
require_config_value "AppData_server.Port" "$UPSTREAM_PORT"
require_port "AppData_server.Port" "$UPSTREAM_PORT"
require_port "AppData_server.ExternalPort" "$EXTERNAL_PORT"

if [[ ! "$DOMAIN" =~ ^[a-zA-Z0-9.-]+$ ]]; then
  echo "AppData_server.Domain may only contain letters, numbers, dot and dash." >&2
  exit 2
fi

if [[ ! "$UPSTREAM_HOST" =~ ^[a-zA-Z0-9_.:-]+$ ]]; then
  echo "AppData_server.BindHost may only contain letters, numbers, underscore, dot, colon and dash." >&2
  exit 2
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run as root, e.g. with sudo." >&2
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script expects a Debian/Ubuntu server with apt-get." >&2
  exit 1
fi

if [[ ! "$SITE_NAME" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
  echo "AppData_server.SiteName may only contain letters, numbers, underscore, dot and dash." >&2
  exit 2
fi

if [[ ! "$CERTBOT_STAGING" =~ ^(true|false)$ ]]; then
  echo "AppData_server.CertbotStaging must be true or false." >&2
  exit 2
fi

UPSTREAM="${UPSTREAM_HOST}:${UPSTREAM_PORT}"
NGINX_AVAILABLE="/etc/nginx/sites-available/${SITE_NAME}.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/${SITE_NAME}.conf"
ACME_WEBROOT="/var/www/certbot/${SITE_NAME}"

echo "Installing Nginx and Certbot packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx certbot python3-certbot-nginx

echo "Preparing ACME webroot at ${ACME_WEBROOT}..."
mkdir -p "${ACME_WEBROOT}/.well-known/acme-challenge"

echo "Writing temporary Nginx HTTP config for ${DOMAIN}..."
cat > "$NGINX_AVAILABLE" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    access_log /var/log/nginx/${SITE_NAME}.access.log;
    error_log /var/log/nginx/${SITE_NAME}.error.log;

    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_WEBROOT};
        default_type "text/plain";
    }

    location / {
        return 301 https://\$host:${EXTERNAL_PORT}\$request_uri;
    }
}
EOF

ln -sfn "$NGINX_AVAILABLE" "$NGINX_ENABLED"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

certbot_args=(
  certonly
  --webroot
  -w "$ACME_WEBROOT"
  --non-interactive
  --agree-tos
  --keep-until-expiring
  -d "$DOMAIN"
)

if [[ -n "$EMAIL" ]]; then
  certbot_args+=(--email "$EMAIL")
else
  echo "No AppData_server.CertbotEmail configured; requesting certificate without registration email."
  certbot_args+=(--register-unsafely-without-email)
fi

if [[ "$CERTBOT_STAGING" == "true" ]]; then
  certbot_args+=(--staging)
fi

echo "Requesting Let's Encrypt certificate for ${DOMAIN}..."
certbot "${certbot_args[@]}"

ssl_options=""
ssl_dhparam=""

if [[ -f /etc/letsencrypt/options-ssl-nginx.conf ]]; then
  ssl_options="    include /etc/letsencrypt/options-ssl-nginx.conf;"
fi

if [[ -f /etc/letsencrypt/ssl-dhparams.pem ]]; then
  ssl_dhparam="    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;"
fi

echo "Writing Nginx reverse proxy config for https://${DOMAIN}:${EXTERNAL_PORT} -> http://${UPSTREAM}..."
cat > "$NGINX_AVAILABLE" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    access_log /var/log/nginx/${SITE_NAME}.access.log;
    error_log /var/log/nginx/${SITE_NAME}.error.log;

    location ^~ /.well-known/acme-challenge/ {
        root ${ACME_WEBROOT};
        default_type "text/plain";
    }

    location / {
        return 301 https://\$host:${EXTERNAL_PORT}\$request_uri;
    }
}

server {
    listen ${EXTERNAL_PORT} ssl http2;
    listen [::]:${EXTERNAL_PORT} ssl http2;
    server_name ${DOMAIN};

    access_log /var/log/nginx/${SITE_NAME}.access.log;
    error_log /var/log/nginx/${SITE_NAME}.error.log;

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
${ssl_options}
${ssl_dhparam}

    add_header Strict-Transport-Security "max-age=31536000" always;

    client_max_body_size 25m;

    location / {
        proxy_pass http://${UPSTREAM};
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
EOF

nginx -t
systemctl reload nginx

echo "Testing automatic certificate renewal..."
certbot renew --dry-run

echo "Done."
echo "Reverse proxy URL: https://${DOMAIN}:${EXTERNAL_PORT}"
echo "Upstream app:      http://${UPSTREAM}"
echo "Config file:       ${CONFIG_FILE}"
echo "Nginx config:      ${NGINX_AVAILABLE}"
