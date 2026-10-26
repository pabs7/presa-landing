#!/bin/sh
# Sustituye en la landing la dirección de la app y el correo de contacto definidos al desplegar.
set -e

export PRESA_APP_URL="${PRESA_APP_URL:-http://localhost}"
export PRESA_CONTACT_EMAIL="${PRESA_CONTACT_EMAIL:-contacto@presaclimb.es}"

page=/usr/share/nginx/html/index.html
envsubst '${PRESA_APP_URL} ${PRESA_CONTACT_EMAIL}' < "$page" > /tmp/index.html
cat /tmp/index.html > "$page"
echo "Presa landing: app en $PRESA_APP_URL, contacto $PRESA_CONTACT_EMAIL"
