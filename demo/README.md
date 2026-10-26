# Capturas de la landing

Las capturas de `landing/img/` salen de un **club demo inventado** («Rocódromo Demo») en el entorno de
desarrollo local. Nunca se sacan de PRE ni de PRO, ni con datos reales.

## Rehacerlas

```bash
docker compose up -d
# 1. Club demo (borra y recrea el club «demo» con fechas relativas a hoy; solo funciona con DEBUG=True)
docker compose exec -T backend python manage.py shell < landing/demo/seed_demo.py
# 2. Capturas en PNG (app en el móvil desde Vite en :5173; panel desde el backend en :8000)
cd e2e && npx playwright test -c capture.config.ts && cd ..
# 3. PNG -> WebP optimizado en landing/img/
docker compose run --rm -v "$PWD/e2e/capture-output:/in" -v "$PWD/landing:/landing" backend \
  python /landing/demo/to_webp.py /in /landing/img
```

Accesos del club demo: `laura@demo.presa.test` (socia) y `admin@demo.presa.test` (administrador),
contraseña `Demo-presa-2026`.

Del panel solo se enseña la importación de socios: el resto del panel aún está en inglés.
