# Infraestructura — Guía de operaciones

Este directorio contiene toda la configuración de entorno: Docker, Compose y archivos de servidor.

---

## Estructura

```
infrastructure/   (raíz del repositorio)
├── Dockerfile                        Imagen custom de Odoo (producción)
├── docker-compose.yml                Servicios: odoo + postgres
├── docker-compose.override.yml       (ignorado por git) Overrides locales personales
├── docker-compose.override.yml.example  Plantilla de override local
├── .env.example                      Plantilla de variables de entorno
├── config/
│   ├── odoo.conf                     (ignorado por git) Config runtime
│   └── odoo.conf.example             Plantilla de config
└── requirements.txt                  Dependencias Python extra de los addons
```

---

## Primera vez

```bash
# 1. Variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 2. Config de Odoo
cp config/odoo.conf.example config/odoo.conf
# Editar config/odoo.conf si es necesario

# 3. Levantar servicios
docker compose up -d

# 4. Verificar logs
docker compose logs -f odoo
```

Odoo estará disponible en **http://localhost:8069** (o el puerto definido en `.env`).

---

## Comandos frecuentes

```bash
# Detener servicios
docker compose down

# Detener y eliminar volúmenes (borra BD y filestore — ¡DESTRUCTIVO!)
docker compose down -v

# Ver logs en tiempo real
docker compose logs -f odoo
docker compose logs -f db

# Acceder a la shell del contenedor de Odoo
docker compose exec odoo bash

# Acceder a psql
docker compose exec db psql -U odoo -d odoo_dev

# Reconstruir la imagen custom (tras cambios en Dockerfile o requirements.txt)
docker compose build odoo
```

---

## Desarrollo vs Producción

| Aspecto | Desarrollo | Producción |
|---|---|---|
| Imagen Odoo | `image: odoo:19.0` (upstream) | `build: .` (Dockerfile custom) |
| `--dev=all` | ✔ Activado en `command` | ✘ Eliminar |
| `workers` | `0` (mono-proceso) | `2`–`4` |
| Credenciales | `.env` local | Secrets del servidor / CI |

Para producción, se recomienda crear un `docker-compose.prod.yml` que sobreescriba los valores de desarrollo y referencie la imagen construida desde el `Dockerfile`.

---

## Override local

Si necesitas personalizar puertos u opciones sin afectar al equipo, usa el override local:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# Editar a gusto — este archivo está en .gitignore
```

Docker Compose fusiona automáticamente `docker-compose.yml` y `docker-compose.override.yml`.

---

_Última actualización: 2026-03-19 · Odoo 19.0 Community_
