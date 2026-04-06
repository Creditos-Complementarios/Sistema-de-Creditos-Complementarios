# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardAsignarResponsable(models.TransientModel):
    _name = 'actividad.wizard.asignar.responsable'
    _description = 'Confirmacion de asignacion de Responsable de Actividad'

    actividad_id = fields.Many2one(
        'actividad.complementaria',
        string='Actividad',
        required=True,
        readonly=True,
    )
    nombre_actividad = fields.Char(
        related='actividad_id.name',
        string='Actividad',
        readonly=True,
    )
    responsable_actual = fields.Many2one(
        related='actividad_id.responsable_actividad_id',
        string='Responsable Actual',
        readonly=True,
    )
    responsable_nuevo_id = fields.Many2one(
        'res.users',
        string='Nuevo Responsable',
        required=True,
        options="{'no_create': True, 'no_quick_create': True}",
    )
    dominio_responsable = fields.Binary(
        compute='_compute_dominio_responsable',
        string='Dominio Responsable',
    )

    @api.depends('actividad_id')
    def _compute_dominio_responsable(self):
        """Calcula el dominio de usuarios con rol Responsable de Actividad."""
        grupo = self.env.ref(
            'actividades_complementarias.group_responsable_actividad',
            raise_if_not_found=False,
        )
        if grupo:
            self.env.cr.execute(
                "SELECT uid FROM res_groups_users_rel WHERE gid = %s",
                (grupo.id,)
            )
            ids = [r[0] for r in self.env.cr.fetchall()]
            dominio = [('id', 'in', ids)] if ids else [('id', '=', False)]
        else:
            dominio = [('id', '=', False)]
        for rec in self:
            rec.dominio_responsable = dominio

    def action_confirmar_asignacion(self):
        """Asigna el responsable y bloquea el campo para futuras modificaciones."""
        self.ensure_one()
        if not self.responsable_nuevo_id:
            raise ValidationError('Debe seleccionar un Responsable de Actividad.')
        self.actividad_id.write({
            'responsable_actividad_id': self.responsable_nuevo_id.id,
            'responsable_bloqueado': True,
        })
        self.actividad_id.message_post(
            body=(
                'Responsable de Actividad asignado: %s. '
                'Este campo ha sido bloqueado y no puede modificarse.'
            ) % self.responsable_nuevo_id.name
        )
        return {'type': 'ir.actions.act_window_close'}
