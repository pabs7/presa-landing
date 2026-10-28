#!/bin/sh
# Comprueba una landing en marcha: responde, lleva la app y el correo configurados y sirve todas sus imágenes.
# Uso: sh check.sh <url-de-la-landing> <url-de-la-app> <correo-de-contacto>
set -eu

if [ $# -ne 3 ]; then
  echo "Uso: sh check.sh <url-de-la-landing> <url-de-la-app> <correo-de-contacto>" >&2
  exit 2
fi
landing=${1%/}
app=$2
email=$3
page=$(mktemp)

fail() { echo "ERROR: $1" >&2; exit 1; }

curl -fsS "$landing/nginx-health" > /dev/null || fail "la landing no responde"
curl -fsS "$landing/" -o "$page"
grep -q "data-app-url=\"$app\"" "$page" || fail "la página no lleva la dirección de la app ($app)"
grep -q "mailto:$email" "$page" || fail "la página no lleva el correo de contacto ($email)"
grep -q '\${PRESA_' "$page" && fail "quedan variables sin sustituir"

# Cada imagen enlazada desde la página existe.
for src in $(grep -o 'src="/\?[^"]*\.\(png\|webp\|jpg\|svg\)"' "$page" | sed 's/^src="\/\?//; s/"$//' | sort -u); do
  curl -fsS -o /dev/null "$landing/$src" || fail "falta la imagen $src"
done

# Las capturas se revalidan en cada visita para que al rehacerlas nadie vea las antiguas.
curl -fsSI "$landing/img/muro.webp" | grep -qi '^cache-control: no-cache' || fail "las capturas se quedan en caché"

echo "Landing OK: $landing"
