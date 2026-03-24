# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

# Mapping: keyword found in departamento.name → (rama_key, group_xmlid)
# Add new departments here — nowhere else in this file needs to change.
DEPT_MAP = [
    ('sistem',   'sistemas',  'actividades_complementarias.group_personal_departamento_sistemas'),
    ('electr',   'electrica', 'actividades_complementarias.group_personal_departamento_electrica'),
    ('biol',     'biologia',  'actividades_complementarias.group_personal_departamento_biologia'),
    ('extraesc', 'extraescolar', 'actividades_complementarias.group_personal_departamento_extraescolar'),
]
# Reverse lookup: rama_key → group_xmlid
RAMA_TO_GROUP = {rama: xmlid for _, rama, xmlid in DEPT_MAP}


class EmpleadoPermiso(models.Model):
    _name = 'actividad.empleado.permiso'
    _description = 'Permisos de Personal por Departamento'
    _inherit = ['mail.thread']
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='Empleado',
        required=True,
        ondelete='cascade',
    )
    no_empleado = fields.Char(string='No. Empleado')
    carrera = fields.Char(string='Carrera')
    departamento_id = fields.Many2one(
        'actividad.departamento',
        string='Departamento',
        required=True,
        ondelete='restrict',
    )

    # Rama / grupo de departamento al que pertenece el empleado
    departamento_grupo = fields.Selection([
        ('sistemas', 'Personal de Departamento de Sistemas'),
        ('electrica', 'Personal de Departamento de Eléctrica'),
        ('biologia', 'Personal de Departamento de Biología'),
    ], string='Rama de Departamento', required=True,
       help='Determina a qué grupo de seguridad pertenece este empleado.')

    # ── Permisos delegables ──────────────────────────────────────────────────
    perm_modificar_actividades = fields.Boolean(
        string='Modificar Actividades Complementarias',
        default=False,
        tracking=True,
    )
    perm_difundir_actividades = fields.Boolean(
        string='Difundir Actividades',
        default=False,
        tracking=True,
    )
    perm_asignar_alumnos = fields.Boolean(
        string='Asignar Alumnos a Actividad',
        default=False,
        tracking=True,
    )
    perm_enviar_catalogo = fields.Boolean(
        string='Enviar al Catálogo',
        default=False,
        tracking=True,
    )
    # NOTA: perm_gestionar_personal NO es delegable

    # ── Control de vencimiento ───────────────────────────────────────────────
    fecha_ultimo_uso = fields.Date(
        string='Último Uso',
        default=fields.Date.today,
    )

    # ── Dominio dinámico para user_id en la vista ────────────────────────────
    dominio_user = fields.Binary(
        compute='_compute_dominio_user',
        string='Dominio Usuario',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    def _compute_dominio_user(self):
        """
        Devuelve dominio para filtrar user_id según la rama del JD en sesión.
        Usa SQL directo para evitar recursión (no llama a search() de este mismo modelo).
        """
        domain = self._get_dominio_user_para_jefe()
        for rec in self:
            rec.dominio_user = domain

    @api.model
    def _get_dominio_user_para_jefe(self):
        """
        Obtiene los IDs de usuarios permitidos para el JD en sesión.
        El JD está registrado en actividad.departamento como jefe_id.
        Detecta su departamento y devuelve los usuarios del grupo correspondiente.
        """
        if self.env.user.has_group('actividades_complementarias.group_admin_actividades'):
            return []  # Admin ve todos los usuarios

        # 1. Buscar el departamento donde el usuario en sesión es Jefe
        self.env.cr.execute(
            "SELECT name FROM actividad_departamento WHERE jefe_id = %s LIMIT 1",
            (self.env.user.id,)
        )
        row = self.env.cr.fetchone()

        grupo_xmlid = None
        if row:
            dept_name = row[0].lower()
            for keyword, _rama, xmlid in DEPT_MAP:
                if keyword in dept_name:
                    grupo_xmlid = xmlid
                    break

        # 2. Fallback: buscar por departamento_grupo en actividad_empleado_permiso
        if not grupo_xmlid:
            self.env.cr.execute(
                "SELECT departamento_grupo FROM actividad_empleado_permiso WHERE user_id = %s LIMIT 1",
                (self.env.user.id,)
            )
            row2 = self.env.cr.fetchone()
            if row2 and row2[0] in RAMA_TO_GROUP:
                grupo_xmlid = RAMA_TO_GROUP[row2[0]]

        if not grupo_xmlid:
            return [('id', '=', False)]

        grupo = self.env.ref(grupo_xmlid, raise_if_not_found=False)
        if not grupo:
            return [('id', '=', False)]

        self.env.cr.execute(
            "SELECT uid FROM res_groups_users_rel WHERE gid = %s",
            (grupo.id,)
        )
        user_ids = [r[0] for r in self.env.cr.fetchall()]
        if not user_ids:
            return [('id', '=', False)]
        return [('id', 'in', user_ids)]

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────

    @api.constrains('user_id', 'departamento_id')
    def _check_mismo_departamento(self):
        for rec in self:
            jefe = rec.departamento_id.jefe_id
            if jefe and rec.user_id == jefe:
                raise ValidationError(
                    'El Jefe de Departamento no debe aparecer en la lista de personal.'
                )

    @api.constrains('user_id', 'departamento_grupo')
    def _check_jefe_solo_asigna_misma_rama(self):
        """Un Jefe de Departamento solo puede asignar empleados de su misma rama."""
        if self.env.user.has_group('actividades_complementarias.group_admin_actividades'):
            return

        self.env.cr.execute(
            "SELECT name FROM actividad_departamento WHERE jefe_id = %s LIMIT 1",
            (self.env.user.id,)
        )
        row_dept = self.env.cr.fetchone()
        rama_jefe = None
        if row_dept:
            for keyword, rama, _xmlid in DEPT_MAP:
                if keyword in row_dept[0].lower():
                    rama_jefe = rama
                    break
        if not rama_jefe:
            self.env.cr.execute(
                "SELECT departamento_grupo FROM actividad_empleado_permiso WHERE user_id = %s LIMIT 1",
                (self.env.user.id,)
            )
            row = self.env.cr.fetchone()
            if row:
                rama_jefe = row[0]
        if not rama_jefe:
            return
        nombres = {rama: rama.capitalize() for _, rama, _ in DEPT_MAP}
        for rec in self:
            if rec.departamento_grupo and rec.departamento_grupo != rama_jefe:
                raise ValidationError(
                    f'Solo puede asignar empleados de su misma rama de departamento '
                    f'({nombres.get(rama_jefe, rama_jefe)}).'
                )

    # ────────────────────────────────────────────────────────────────────────
    # ORM overrides — filtrado automático por rama en la lista
    # ────────────────────────────────────────────────────────────────────────

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        """
        Restringe la lista a registros del mismo departamento para el JD.
        Usa SQL directo para obtener la rama y así evitar recursión.
        """
        if not self.env.user.has_group('actividades_complementarias.group_admin_actividades'):
            grupo_xmlid = None
            self.env.cr.execute(
                "SELECT name FROM actividad_departamento WHERE jefe_id = %s LIMIT 1",
                (self.env.user.id,)
            )
            row_dept = self.env.cr.fetchone()
            if row_dept:
                for keyword, _rama, xmlid in DEPT_MAP:
                    if keyword in row_dept[0].lower():
                        grupo_xmlid = xmlid
                        break
            if not grupo_xmlid:
                self.env.cr.execute(
                    "SELECT departamento_grupo FROM actividad_empleado_permiso WHERE user_id = %s LIMIT 1",
                    (self.env.user.id,)
                )
                row2 = self.env.cr.fetchone()
                if row2 and row2[0] in RAMA_TO_GROUP:
                    grupo_xmlid = RAMA_TO_GROUP[row2[0]]
            if grupo_xmlid:
                grupo = self.env.ref(grupo_xmlid, raise_if_not_found=False)
                if grupo:
                    self.env.cr.execute(
                        "SELECT uid FROM res_groups_users_rel WHERE gid = %s",
                        (grupo.id,)
                    )
                    user_ids = [r[0] for r in self.env.cr.fetchall()]
                    if user_ids:
                        domain = [('user_id', 'in', user_ids)] + list(domain)

        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)

    # ────────────────────────────────────────────────────────────────────────
    # Auto-sync: puebla la lista con empleados del mismo departamento
    # ────────────────────────────────────────────────────────────────────────

    @api.model
    def sincronizar_personal_departamento(self):
        """
        Crea registros de EmpleadoPermiso para todos los usuarios que pertenezcan
        al grupo de seguridad del departamento del JD en sesión, si aún no existen.
        Excluye al propio Jefe de Departamento.
        """
        if self.env.user.has_group('actividades_complementarias.group_admin_actividades'):
            return  # El admin no necesita auto-sync

        # 1. Detectar departamento del JD en sesión
        self.env.cr.execute(
            "SELECT id, name FROM actividad_departamento WHERE jefe_id = %s LIMIT 1",
            (self.env.user.id,)
        )
        row_dept = self.env.cr.fetchone()
        if not row_dept:
            return

        dept_id, dept_name = row_dept
        dept_name_lower = dept_name.lower()

        rama = None
        grupo_xmlid = None
        for keyword, rama_key, xmlid in DEPT_MAP:
            if keyword in dept_name_lower:
                rama = rama_key
                grupo_xmlid = xmlid
                break

        if not grupo_xmlid or not rama:
            return

        grupo = self.env.ref(grupo_xmlid, raise_if_not_found=False)
        if not grupo:
            return

        # 2. Obtener usuarios del grupo (excluyendo al JD)
        self.env.cr.execute(
            "SELECT uid FROM res_groups_users_rel WHERE gid = %s",
            (grupo.id,)
        )
        user_ids_en_grupo = [r[0] for r in self.env.cr.fetchall()]
        user_ids_en_grupo = [uid for uid in user_ids_en_grupo if uid != self.env.user.id]

        if not user_ids_en_grupo:
            return

        # 3. Obtener usuarios que ya tienen registro en este departamento
        self.env.cr.execute(
            "SELECT user_id FROM actividad_empleado_permiso WHERE departamento_grupo = %s",
            (rama,)
        )
        ya_registrados = {r[0] for r in self.env.cr.fetchall()}

        # 4. Crear registros para los que faltan
        for uid in user_ids_en_grupo:
            if uid in ya_registrados:
                continue
            user = self.env['res.users'].browse(uid)
            if not user.exists():
                continue
            self.sudo().create({
                'user_id': uid,
                'no_empleado': '',
                'departamento_id': dept_id,
                'departamento_grupo': rama,
            })

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kwargs):
        """Sincroniza personal antes de devolver la lista."""
        self.sincronizar_personal_departamento()
        return super().search_read(
            domain=domain, fields=fields, offset=offset,
            limit=limit, order=order, **kwargs
        )

    # ────────────────────────────────────────────────────────────────────────
    # Business logic
    # ────────────────────────────────────────────────────────────────────────

    def action_guardar_permisos(self):
        """Guarda el registro actual y regresa a la lista."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestion de Personal',
            'res_model': 'actividad.empleado.permiso',
            'view_mode': 'list,kanban,form',
            'target': 'current',
        }

    def action_regresar_lista(self):
        """Regresa a la lista sin guardar cambios adicionales."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gestion de Personal',
            'res_model': 'actividad.empleado.permiso',
            'view_mode': 'list,kanban,form',
            'target': 'current',
        }

    def _remover_permisos_inactivos(self):
        """Cron: remueve permisos de empleados sin uso en los últimos 30 días."""
        limite = date.today() - timedelta(days=30)
        inactivos = self.search([('fecha_ultimo_uso', '<', limite)])
        inactivos.write({
            'perm_modificar_actividades': False,
            'perm_difundir_actividades': False,
            'perm_asignar_alumnos': False,
            'perm_enviar_catalogo': False,
        })
        for emp in inactivos:
            emp.message_post(
                body='Permisos removidos automáticamente por 30 días de inactividad.'
            )
