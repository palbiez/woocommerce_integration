#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  sudo bash scripts/setup-reverse-proxy-tls.sh \
    --domain integration.example.com \
    --email admin@example.com \
    [--upstream 127.0.0.1:8000] \
    [--site-name wci] \
    [--staging]

Sets up Nginx as TLS reverse proxy for the WooCommerce/Etsy integration app.

Assumptions:
  - Debian/Ubuntu server with apt
  - DNS A/AAAA record for --domain already points to this server
  - Ports 80 and 443 are reachable from the internet
  - The app listens only locally, e.g. 127.0.0.1:8000
EOF
}

require_value() {
  local name="$1"
  local value="${2:-}"
  if [[ -z "$value" || "$value" == --* ]]; then
    echo "Missing value for $name" >&2
    usage
    exit 2
  fi
}

DOMAIN=""
EMAIL=""
UPSTREAM="127.0.0.1:8000"
SITE_NAME="wci"
CERTBOT_STAGING="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --domain)
      require_value "$1" "${2:-}"
      DOMAIN="$2"
      shift 2
      ;;
    --email)
      require_value "$1" "${2:-}"
      EMAIL="$2"
      shift 2
      ;;
    --upstream)
      require_value "$1" "${2:-}"
      UPSTREAM="$2"
      shift 2
      ;;
    --site-name)
      require_value "$1" "${2:-}"
      SITE_NAME="$2"
      shift 2
      ;;
    --staging)
      CERTBOT_STAGING="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Please run as root, e.g. with sudo." >&2
  exit 1
fi

if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "--domain and --email are required." >&2
  usage
  exit 2
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script expects a Debian/Ubuntu server with apt-get." >&2
  exit 1
fi

if [[ ! "$SITE_NAME" =~ ^[a-zA-Z0-9_.-]+$ ]]; then
  echo "--site-name may only contain letters, numbers, underscore, dot and dash." >&2
  exit 2
fi

NGINX_AVAILABLE="/etc/nginx/sites-available/${SITE_NAME}.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/${SITE_NAME}.conf"

echo "Installing Nginx and Certbot packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx certbot python3-certbot-nginx

echo "Writing Nginx reverse proxy config for ${DOMAIN} -> http://${UPSTREAM}..."
cat > "$NGINX_AVAILABLE" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    access_log /var/log/nginx/${SITE_NAME}.access.log;
    error_log /var/log/nginx/${SITE_NAME}.error.log;

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

ln -sfn "$NGINX_AVAILABLE" "$NGINX_ENABLED"
nginx -t
systemctl enable --now nginx
systemctl reload nginx

certbot_args=(
  --nginx
  --non-interactive
  --agree-tos
  --email "$EMAIL"
  --redirect
  --hsts
  -d "$DOMAIN"
)

if [[ "$CERTBOT_STAGING" == "true" ]]; then
  certbot_args+=(--staging)
fi

echo "Requesting Let's Encrypt certificate for ${DOMAIN}..."
certbot "${certbot_args[@]}"

echo "Testing automatic certificate renewal..."
certbot renew --dry-run

echo "Done."
echo "Reverse proxy URL: https://${DOMAIN}"
echo "Upstream app:      http://${UPSTREAM}"
echo "Nginx config:      ${NGINX_AVAILABLE}"
