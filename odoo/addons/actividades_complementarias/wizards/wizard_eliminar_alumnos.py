# -*- coding: utf-8 -*-
from odoo import models, fields


class WizardEliminarAlumnosLinea(models.TransientModel):
    _name = 'actividad.wizard.eliminar.alumnos.linea'
    _description = 'Linea de alumno a eliminar'

    wizard_id = fields.Many2one(
        'actividad.wizard.eliminar.alumnos', ondelete='cascade'
    )
    alumno_id = fields.Many2one('res.users', string='Alumno', required=True)
    login = fields.Char(
        related='alumno_id.login', string='Correo', readonly=True
    )
    a_eliminar = fields.Boolean(string='Eliminar', default=False)


class WizardEliminarAlumnos(models.TransientModel):
    _name = 'actividad.wizard.eliminar.alumnos'
    _description = 'Eliminar Alumnos de Actividad'

    actividad_id = fields.Many2one(
        'actividad.complementaria', required=True
    )
    linea_ids = fields.One2many(
        'actividad.wizard.eliminar.alumnos.linea',
        'wizard_id',
        string='Alumnos',
    )

    def action_confirmar(self):
        self.ensure_one()
        eliminar_ids = self.linea_ids.filtered(
            lambda linea: linea.a_eliminar
        ).mapped('alumno_id').ids
        self.actividad_id.with_context(
            bypass_edit_protection=True
        ).write({
            'alumno_ids': [(3, uid) for uid in eliminar_ids],
        })
        return {'type': 'ir.actions.act_window_close'}
