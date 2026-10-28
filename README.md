# Presa · landing

Página pública de Presa (presaclimb.es): estática, servida por nginx en un contenedor.

## Probar en local

```bash
docker build -t presa-landing .
docker run --rm -p 8081:80 -e PRESA_APP_URL=http://localhost:5173 presa-landing
sh check.sh http://localhost:8081 http://localhost:5173 contacto@presaclimb.es
```

Abre http://localhost:8081.

## Configuración

| Variable | Para qué | Por defecto |
|---|---|---|
| `PRESA_APP_URL` | Dirección de la app («Entrar», «Instalar la app») | `http://localhost` |
| `PRESA_CONTACT_EMAIL` | Correo de los botones de contacto | `contacto@presaclimb.es` |

## Despliegue

Solo `main`, en PRO (Dokploy, aplicación de tipo Dockerfile). El despliegue es manual: botón Deploy.

## Capturas

Las capturas de `img/` salen del club demo de la app. Se generan desde el repositorio `presa` (`tools/landing-demo/`) y se copian aquí.
