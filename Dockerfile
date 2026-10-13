# Landing pública de Presa: página estática servida por nginx. Se construye desde la raíz del repo.
FROM nginx:1.30-alpine

# Parches de seguridad del sistema publicados después de la imagen base.
RUN apk upgrade --no-cache

COPY landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY landing/index.html landing/styles.css landing/main.js landing/app-screenshot.webp /usr/share/nginx/html/
COPY frontend/public/presa-logo.png frontend/public/apple-touch-icon.png /usr/share/nginx/html/
COPY landing/docker-entrypoint.d/40-presa-landing-config.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/40-presa-landing-config.sh

EXPOSE 80
