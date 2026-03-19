# Módulos Odoo — Guía de Desarrollo

Este directorio contiene exclusivamente los módulos Odoo personalizados desarrollados para el proyecto. El código fuente de Odoo Community no está aquí — se referencia como imagen Docker desde `infra/`.

---

## Contenido

```
odoo/
├── README.md               ← este archivo
└── addons/
    ├── modulo_uno/
    │   ├── __manifest__.py
    │   ├── __init__.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── sale_order.py
    │   ├── views/
    │   │   └── sale_order_views.xml
    │   ├── security/
    │   │   ├── ir.model.access.csv
    │   │   └── security.xml
    │   ├── data/
    │   │   └── data.xml
    │   ├── tests/
    │   │   ├── __init__.py
    │   │   └── test_sale_order.py
    │   └── static/
    │       └── description/
    │           └── icon.png
    └── modulo_dos/
        └── ...
```

---

## Módulos del proyecto

| Módulo | Descripción | Depende de | Responsable |
|---|---|---|---|
| `modulo_uno` | _Descripción breve_ | `sale`, `account` | Back-end |
| `modulo_dos` | _Descripción breve_ | `stock` | Back-end |

_Mantener esta tabla actualizada al añadir o deprecar módulos._

---

## Configuración del entorno

El entorno de ejecución vive en `infra/`. Para levantar Odoo con los módulos de este directorio montados:

```bash
# Desde la raíz del repositorio
docker compose -f infra/docker-compose.yml up -d
```

Odoo monta `odoo/addons/` como volumen en `/mnt/extra-addons` dentro del contenedor.

---

## Operaciones comunes

### Instalar un módulo

```bash
docker compose -f infra/docker-compose.yml exec odoo \
  odoo-bin -d odoo_dev -i nombre_modulo --stop-after-init
```

### Actualizar un módulo tras cambios

```bash
docker compose -f infra/docker-compose.yml exec odoo \
  odoo-bin -d odoo_dev -u nombre_modulo --stop-after-init
```

### Ejecutar los tests de un módulo

```bash
docker compose -f infra/docker-compose.yml exec odoo \
  odoo-bin -d odoo_dev --test-tags nombre_modulo --stop-after-init --log-level=test
```

### Ejecutar tests de todos los módulos del proyecto

```bash
docker compose -f infra/docker-compose.yml exec odoo \
  odoo-bin -d odoo_dev \
  --test-tags modulo_uno,modulo_dos \
  --stop-after-init --log-level=test
```

### Correr linting localmente antes de un PR

```bash
# Desde la raíz del repositorio
docker compose -f infra/docker-compose.yml exec odoo \
  python -m flake8 /mnt/extra-addons/ --max-line-length=120 --exclude=__pycache__
```

---

## Estándares de código

### Python

- Seguir [OCA Guidelines](https://github.com/OCA/odoo-community.org/blob/master/website/Contribution/CONTRIBUTING.rst) como referencia base.
- Máximo 120 caracteres por línea.
- Todas las clases de modelo deben tener `_description`.
- No usar `sudo()` sin un comentario que justifique el bypass de seguridad.
- Los métodos privados llevan prefijo `_`.

```python
# ✔ Correcto
class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'
    _description = 'Pedido de venta con márgenes'

    margin = fields.Float(
        string='Margen (%)',
        compute='_compute_margin',
        store=True,
    )

    @api.depends('order_line.margin')
    def _compute_margin(self):
        for order in self:
            # lógica de cálculo
            pass
```

### XML (vistas)

- Un archivo por modelo o agrupación funcional coherente.
- Los `id` de los registros siguen el patrón `<modulo>_<modelo>_<tipo>` (ej. `modulo_uno_sale_order_form`).
- No modificar vistas estándar de Odoo con `<attribute>` si un `<xpath>` es posible — es más resistente a actualizaciones.

```xml
<!-- ✔ Correcto: usar xpath sobre attribute cuando aplique -->
<record id="modulo_uno_sale_order_form" model="ir.ui.view">
    <field name="name">sale.order.form.modulo_uno</field>
    <field name="model">sale.order</field>
    <field name="inherit_id" ref="sale.view_order_form"/>
    <field name="arch" type="xml">
        <xpath expr="//field[@name='amount_total']" position="after">
            <field name="margin"/>
        </xpath>
    </field>
</record>
```

### `__manifest__.py`

Campos obligatorios en todo módulo:

```python
{
    'name': 'Nombre legible del módulo',
    'version': '19.0.1.0.0',       # <odoo_version>.<major>.<minor>.<patch>.<fix>
    'summary': 'Una línea descriptiva',
    'author': 'Nombre del equipo / empresa',
    'license': 'LGPL-3',
    'depends': ['base', 'sale'],   # dependencias mínimas necesarias
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,          # True solo si es un módulo de aplicación principal
}
```

### Seguridad

Cada modelo nuevo requiere una entrada en `security/ir.model.access.csv`:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mi_modelo_user,mi.modelo.user,model_mi_modelo,base.group_user,1,0,0,0
access_mi_modelo_manager,mi.modelo.manager,model_mi_modelo,base.group_system,1,1,1,1
```

No otorgar permisos más amplios de los necesarios. Documentar en un comentario si un grupo requiere acceso inusual.

---

## Convenciones de nombres de módulos

Los módulos del proyecto siguen el patrón:

```
<prefijo_proyecto>_<dominio_funcional>
```

Donde `<prefijo_proyecto>` es una abreviatura de 2–4 letras acordada al inicio del proyecto (ej. `acm` para Acme Corp).

**Ejemplos:**

```
acm_sale         Personalizaciones de ventas
acm_account      Personalizaciones de contabilidad
acm_stock        Personalizaciones de inventario
acm_portal       Customizaciones del portal web
```

---

## Migraciones de base de datos

Los scripts de migración viven dentro del módulo correspondiente:

```
modulo_uno/
└── migrations/
    └── 19.0.2.0.0/
        ├── pre-migrate.py     # Corre antes de la actualización del modelo
        └── post-migrate.py    # Corre después de la actualización del modelo
```

### Reglas para migraciones

- Cada migración corresponde a un cambio de versión en `__manifest__.py`.
- Los scripts de migración **sí se versionan** — son código, no datos generados.
- Los scripts deben ser idempotentes: correr dos veces no debe romper nada.
- Probar la migración en una copia de la base de datos de producción antes de abrir el PR.
- Incluir en el PR una descripción del cambio de esquema y cómo revertirlo si falla.

```python
# migrations/19.0.2.0.0/post-migrate.py
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Poblar el nuevo campo 'margin' en pedidos existentes."""
    _logger.info("Calculando márgenes para pedidos existentes...")
    cr.execute("""
        UPDATE sale_order
        SET margin = 0.0
        WHERE margin IS NULL
    """)
    _logger.info("Migración completada: %d pedidos actualizados", cr.rowcount)
```

---

## Tests

Cada módulo debe tener al menos un archivo de tests en `tests/`. Se usan los mecanismos estándar de Odoo (`TransactionCase`, `SavepointCase`).

```python
# tests/test_sale_order.py
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('modulo_uno', '-standard')
class TestSaleOrderMargin(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})

    def test_margin_computed(self):
        """El margen debe calcularse al confirmar el pedido."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        self.assertGreaterEqual(order.margin, 0)
```

### Convención de tags

Etiquetar cada clase de test con el nombre del módulo para poder ejecutar tests por módulo de forma selectiva en CI.

---

## Checklist antes de abrir un PR

- [ ] `__manifest__.py` tiene la versión correcta y las dependencias mínimas.
- [ ] Todos los modelos nuevos tienen entradas en `ir.model.access.csv`.
- [ ] Los tests pasan localmente con `--test-tags nombre_modulo`.
- [ ] El linting no reporta errores (`flake8`).
- [ ] No hay `print()`, `_logger.warning('TODO')` ni código comentado en el diff.
- [ ] Si hay cambios de esquema, existe el script de migración correspondiente.
- [ ] Si se añade una dependencia Python, está registrada en `requirements.txt` en la raíz.

---

_Última actualización: 2026-03-17 · Odoo 19.0 Community_
