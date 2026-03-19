# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


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

    # ── Control de vencimiento ───────────────────────────────────────────────
    fecha_ultimo_uso = fields.Date(
        string='Último Uso',
        default=fields.Date.today,
    )

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

    # ────────────────────────────────────────────────────────────────────────
    # Business logic
    # ────────────────────────────────────────────────────────────────────────

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
