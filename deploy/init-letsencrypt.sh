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

echo "### Generando configuración TLS recomendada ..."
# Se genera localmente (en vez de descargarla de GitHub) para no depender de
# una ruta externa que puede cambiar o desaparecer sin aviso.
mkdir -p ./deploy/certbot-conf
if [ ! -s ./deploy/certbot-conf/options-ssl-nginx.conf ]; then
    cat > ./deploy/certbot-conf/options-ssl-nginx.conf <<'TLSCONF'
ssl_session_cache shared:le_nginx_SSL:10m;
ssl_session_timeout 1440m;
ssl_session_tickets off;

ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;

ssl_ciphers "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384";
TLSCONF
fi
if [ ! -s ./deploy/certbot-conf/ssl-dhparam.pem ]; then
    openssl dhparam -out ./deploy/certbot-conf/ssl-dhparam.pem 2048
fi

echo "### Creando certificado autofirmado temporal para poder levantar nginx ..."
CERT_PATH="/etc/letsencrypt/live/$DOMAIN"
$COMPOSE run --rm --entrypoint sh certbot -c "
  mkdir -p $CERT_PATH &&
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout '$CERT_PATH/privkey.pem' \
    -out '$CERT_PATH/fullchain.pem' \
    -subj '/CN=localhost'"

echo "### Copiando la configuración TLS al volumen compartido con nginx ..."
$COMPOSE run --rm --entrypoint sh \
  -v "$(pwd)/deploy/certbot-conf:/tmp:ro" certbot -c "
  cp /tmp/options-ssl-nginx.conf /etc/letsencrypt/options-ssl-nginx.conf &&
  cp /tmp/ssl-dhparam.pem /etc/letsencrypt/ssl-dhparam.pem"

echo "### Levantando nginx con el certificado temporal ..."
$COMPOSE up -d nginx
sleep 3
if ! $COMPOSE ps nginx | grep -q "Up"; then
    echo "nginx no arrancó, revisa los logs: docker compose -f docker-compose.prod.yml logs nginx" >&2
    exit 1
fi

echo "### Eliminando el certificado temporal ..."
$COMPOSE run --rm --entrypoint sh certbot -c "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf"

echo "### Solicitando el certificado real a Let's Encrypt ..."
# El servicio "certbot" del compose tiene su propio entrypoint (el bucle de
# renovación); hay que pisarlo explícitamente para correr un comando suelto.
$COMPOSE run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$CERTBOT_EMAIL" \
    --rsa-key-size 2048 \
    --agree-tos \
    --no-eff-email

echo "### Recargando nginx con el certificado definitivo ..."
$COMPOSE exec nginx nginx -s reload

echo "Listo. https://$DOMAIN debería estar sirviendo con HTTPS."
