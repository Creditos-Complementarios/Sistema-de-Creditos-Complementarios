# Actividades Complementarias

Módulo Odoo 19 Community para la gestión integral de actividades complementarias institucionales.

## Casos de uso implementados

| ID       | Módulo                                          | Prioridad |
|----------|-------------------------------------------------|-----------|
| JD-01SC  | Solicitud de nuevo tipo de actividad            | Alta      |
| JD-02SC  | Gestión de actividades complementarias          | Alta      |
| JD-03SC  | Gestión de personal para asignación de permisos | Alta      |

## Modelos principales

| Modelo                          | Descripción                                      |
|---------------------------------|--------------------------------------------------|
| `actividad.complementaria`      | Entidad principal de actividad                   |
| `actividad.propuesta`           | Propuesta al Comité Académico                    |
| `actividad.tipo`                | Catálogo de tipos (predefinidos / nuevos)        |
| `actividad.estado`              | Estados del ciclo de vida de la actividad        |
| `actividad.estado.solicitud`    | Estados de propuesta (en revisión/aprobada/rechazada) |
| `actividad.empleado.permiso`    | Permisos delegados por el JD a su personal       |
| `actividad.departamento`        | Catálogo de departamentos                        |

## Grupos de seguridad

- **Jefe de Departamento** – Crea actividades, gestiona propuestas, delega permisos y firma constancias.
- **Comité Académico** – Aprueba o rechaza propuestas de nuevas actividades.
- **Personal de Departamento** – Acceso delegado según permisos otorgados por el JD.

## Automatizaciones (Cron)

| Cron                          | Frecuencia | Regla de negocio                                 |
|-------------------------------|------------|--------------------------------------------------|
| Actualizar estados por fecha  | Diario     | Pendiente→En Curso al llegar fecha inicio; En Curso→Finalizada al llegar fecha fin |
| Auto-aprobar propuestas       | Diario     | Aprueba propuestas sin respuesta tras 5 días     |
| Remover permisos inactivos    | Diario     | Quita permisos a personal sin uso en 30 días     |

## Instalación

```bash
# Copiar módulo al directorio de addons
cp -r actividades_complementarias /path/to/odoo/custom-addons/

# Instalar desde interfaz Odoo:
# Ajustes → Aplicaciones → Buscar "Actividades Complementarias" → Instalar
```

## Dependencias

- `base`
- `mail` (chatter y seguimiento)
