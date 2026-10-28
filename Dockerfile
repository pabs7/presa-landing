# Landing pública de Presa: página estática servida por nginx.
FROM nginx:1.30-alpine

# Parches de seguridad del sistema publicados después de la imagen base.
RUN apk upgrade --no-cache

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html styles.css main.js presa-logo.png apple-touch-icon.png /usr/share/nginx/html/
COPY img/ /usr/share/nginx/html/img/
COPY docker-entrypoint.d/40-presa-landing-config.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/40-presa-landing-config.sh

EXPOSE 80
