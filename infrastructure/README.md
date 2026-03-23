# Infraestructura — Guía de operaciones

Este directorio contiene toda la configuración de entorno: Docker, Compose y archivos de servidor.

---

## Estructura

```
infrastructure/
├── Dockerfile                           Imagen custom de Odoo (producción)
├── docker-compose.yml                   Servicios: odoo + postgres
├── docker-compose.override.yml          (ignorado por git) Overrides locales personales
├── docker-compose.override.yml.example  Plantilla de override local
└── config/
    ├── odoo.conf                        (ignorado por git) Config runtime
    └── odoo.conf.example                Plantilla de config
```

Los archivos `.env` y `.env.example` viven en la **raíz del repositorio**, no aquí.

---

## ⚠️ Dónde ejecutar los comandos

**Todos los comandos `docker compose` deben ejecutarse desde dentro de `infrastructure/`**, no desde la raíz del repositorio.

```bash
cd infrastructure
docker compose up -d
```

Esto es necesario porque `docker-compose.yml` usa rutas relativas (`../odoo/addons`, `./config/odoo.conf`) que se resuelven desde la ubicación del propio archivo. Si se ejecuta desde la raíz, Docker no encontrará el archivo compose y creará directorios vacíos en lugar de montar los volúmenes correctos — lo que hace que Odoo arranque sin encontrar ningún módulo personalizado.

**Si ves directorios `infrastructure/infrastructure/`, `infrastructure/odoo/` o `infrastructure/addons/` en tu repositorio**, es porque Docker los creó automáticamente al intentar montar rutas que no existían. Bórralos:

```bash
rm -rf infrastructure/infrastructure infrastructure/odoo infrastructure/addons
```

Están en `.gitignore` para evitar que se versionen.

---

## Primera vez

```bash
# 1. Variables de entorno (desde la raíz del repositorio)
cp .env.example .env
# Editar .env con tus valores locales

# 2. Entrar a infrastructure/ — TODOS los comandos docker se ejecutan desde aquí
cd infrastructure

# 3. Config de Odoo
cp config/odoo.conf.example config/odoo.conf

# 4. Levantar servicios
docker compose up -d

# 5. Verificar que Odoo encontró los addons
docker compose logs odoo | grep "addons paths"
# Debe aparecer '/mnt/extra-addons' en la lista
```

Odoo estará disponible en **http://localhost:8069** (o el puerto definido en `.env`).

---

## Comandos frecuentes

Todos desde `infrastructure/`:

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

| Aspecto        | Desarrollo                    | Producción                          |
|----------------|-------------------------------|-------------------------------------|
| Imagen Odoo    | `image: odoo:19.0` (upstream) | `build: .` (Dockerfile custom)      |
| `--dev=all`    | ✔ Activado en `command`       | ✘ Eliminar                          |
| `workers`      | `0` (mono-proceso)            | `2`–`4`                             |
| Credenciales   | `.env` local                  | Secrets del servidor / CI           |

---

## Override local

Si necesitas personalizar puertos u opciones sin afectar al equipo:

```bash
# Desde infrastructure/
cp docker-compose.override.yml.example docker-compose.override.yml
# Editar a gusto — este archivo está en .gitignore
```

Docker Compose fusiona automáticamente `docker-compose.yml` y `docker-compose.override.yml`.

---

_Última actualización: 2026-03-22 · Odoo 19.0 Community_
