# Landing pública de Presa: página estática servida por nginx. Se construye desde la raíz del repo.
FROM nginx:1.27-alpine

COPY landing/nginx.conf /etc/nginx/conf.d/default.conf
COPY landing/index.html landing/styles.css landing/main.js /usr/share/nginx/html/
COPY frontend/public/presa-logo.png frontend/public/apple-touch-icon.png /usr/share/nginx/html/
COPY landing/docker-entrypoint.d/40-presa-landing-config.sh /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/40-presa-landing-config.sh

EXPOSE 80
