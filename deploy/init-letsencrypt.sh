#!/bin/bash
# Bootstrap del certificado HTTPS con Let's Encrypt.
# Correr UNA SOLA VEZ en el VPS, después de que el dominio ya apunte a su IP
# y antes de dejar el stack corriendo de forma permanente. Ver DEPLOY.md.
#
# Uso: ./deploy/init-letsencrypt.sh

set -e

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Falta el archivo .env en la raíz del proyecto (copia .env.example)." >&2
    exit 1
fi

# shellcheck disable=SC1091
source .env

if [ -z "$DOMAIN" ] || [ -z "$CERTBOT_EMAIL" ]; then
    echo "Define DOMAIN y CERTBOT_EMAIL en .env antes de correr este script." >&2
    exit 1
fi

COMPOSE="docker compose -f docker-compose.prod.yml"

echo "### Descargando configuración TLS recomendada de Let's Encrypt ..."
mkdir -p ./deploy/certbot-conf
if [ ! -e ./deploy/certbot-conf/options-ssl-nginx.conf ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > ./deploy/certbot-conf/options-ssl-nginx.conf
fi
if [ ! -e ./deploy/certbot-conf/ssl-dhparam.pem ]; then
    curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/ssl-dhparam.pem > ./deploy/certbot-conf/ssl-dhparam.pem
fi

echo "### Creando certificado autofirmado temporal para poder levantar nginx ..."
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
$COMPOSE run --rm --entrypoint "\
  mkdir -p $CERT_PATH && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '$CERT_PATH/privkey.pem' \
    -out '$CERT_PATH/fullchain.pem' \
    -subj '/CN=localhost'" certbot

echo "### Copiando la configuración TLS al volumen compartido con nginx ..."
$COMPOSE run --rm --entrypoint "\
  cp /tmp/options-ssl-nginx.conf /etc/letsencrypt/options-ssl-nginx.conf && \
  cp /tmp/ssl-dhparam.pem /etc/letsencrypt/ssl-dhparam.pem" \
  -v "$(pwd)/deploy/certbot-conf:/tmp:ro" certbot

echo "### Levantando nginx con el certificado temporal ..."
$COMPOSE up -d nginx

echo "### Eliminando el certificado temporal ..."
$COMPOSE run --rm --entrypoint "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

echo "### Solicitando el certificado real a Let's Encrypt ..."
$COMPOSE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    -d $DOMAIN \
    --email $CERTBOT_EMAIL \
    --rsa-key-size 2048 \
    --agree-tos \
    --no-eff-email" certbot

echo "### Recargando nginx con el certificado definitivo ..."
$COMPOSE exec nginx nginx -s reload

echo "Listo. https://$DOMAIN debería estar sirviendo con HTTPS."
