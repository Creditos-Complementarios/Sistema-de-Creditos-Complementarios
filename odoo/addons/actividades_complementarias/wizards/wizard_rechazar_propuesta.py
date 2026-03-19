# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError


class WizardRechazarPropuesta(models.TransientModel):
    """Wizard para capturar el motivo de rechazo de una propuesta."""
    _name = 'actividad.wizard.rechazar'
    _description = 'Wizard: Rechazar Propuesta'

    propuesta_id = fields.Many2one('actividad.propuesta', string='Propuesta', required=True)
    motivo_rechazo = fields.Text(string='Motivo de Rechazo', required=True)

    def action_confirmar_rechazo(self):
        self.ensure_one()
        if not self.motivo_rechazo or not self.motivo_rechazo.strip():
            raise ValidationError('El motivo de rechazo es obligatorio.')
        self.propuesta_id.write({'motivo_rechazo': self.motivo_rechazo})
        self.propuesta_id.action_rechazar()
        return {'type': 'ir.actions.act_window_close'}
