## Descripción

_¿Qué cambia y por qué?_

## Módulo(s) afectado(s)

- `acm_modulo`

## Tipo de cambio

- [ ] `feat` — Nueva funcionalidad
- [ ] `fix` — Corrección de bug
- [ ] `refactor` — Sin cambio funcional
- [ ] `docs` — Solo documentación
- [ ] `test` — Solo tests
- [ ] `chore` — CI, dependencias, configuración

## Checklist

- [ ] `__manifest__.py` tiene versión correcta y dependencias mínimas
- [ ] Modelos nuevos tienen entradas en `ir.model.access.csv`
- [ ] Tests pasan localmente (`--test-tags nombre_modulo`)
- [ ] Linting sin errores (`flake8`)
- [ ] No hay `print()`, TODOs ni código comentado en el diff
- [ ] Si hay cambios de esquema, existe el script de migración
- [ ] Si se añade dependencia Python, está en `requirements.txt`

## Cómo probar

_Pasos para verificar el cambio manualmente._

## Notas para el revisor

_Contexto adicional, decisiones de diseño, trade-offs._
