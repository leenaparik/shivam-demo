#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

APP_DIR="/opt/shivam-demo"
REPO_URL="https://github.com/leenaparik/shivam-demo.git"

log() {
  echo "[$(date -Is)] $*"
}

log "Updating packages..."
apt-get update -y

log "Installing docker, docker-compose, git..."
apt-get install -y docker.io docker-compose git ca-certificates curl python3
systemctl enable --now docker

log "Cloning repo..."
rm -rf "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

log "Creating .env..."
cp -f env.example .env

# External IP (for correct CORS origin)
EXTERNAL_IP="$(curl -fsS -H 'Metadata-Flavor: Google' \
  'http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip')"

# Generate Fernet key (urlsafe base64 of 32 bytes) without extra deps
SSN_KEY="$(python3 - <<'PY'
import os, base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
)"

# Random-ish Flask secret
FLASK_SECRET_KEY="$(python3 - <<'PY'
import os, base64
print(base64.urlsafe_b64encode(os.urandom(32)).decode())
PY
)"

sed -i "s|^UI_ORIGIN=.*$|UI_ORIGIN=http://${EXTERNAL_IP}:8080|g" .env || true
sed -i "s|^SSN_KEY=.*$|SSN_KEY=${SSN_KEY}|g" .env || true
sed -i "s|^FLASK_SECRET_KEY=.*$|FLASK_SECRET_KEY=${FLASK_SECRET_KEY}|g" .env || true

log "Starting containers..."
# Ensure old containers like phpMyAdmin are removed if the compose file changed.
docker-compose down --remove-orphans || true
docker-compose up -d --build --remove-orphans

log "Done."
log "UI:        http://${EXTERNAL_IP}:8080"
log "Employees: http://${EXTERNAL_IP}:8080/employees.html"
log "API:       http://${EXTERNAL_IP}:5000/api/health"
log "phpMyAdmin:http://${EXTERNAL_IP}:8081"


