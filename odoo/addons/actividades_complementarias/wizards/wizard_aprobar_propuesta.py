# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WizardAprobarPropuesta(models.TransientModel):
    """Wizard para asignar creditos al aprobar una propuesta."""
    _name = 'actividad.wizard.aprobar'
    _description = 'Wizard: Aprobar Propuesta'

    propuesta_id = fields.Many2one('actividad.propuesta', string='Propuesta', required=True)
    nombre_actividad = fields.Char(string='Actividad', readonly=True)
    creditos = fields.Selection([
        ('0.5', '0.5 créditos'),
        ('1.0', '1 crédito'),
        ('1.5', '1.5 créditos'),
        ('2.0', '2 créditos'),
    ], string='Créditos Asignados', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        propuesta_id = res.get('propuesta_id') or self.env.context.get('default_propuesta_id')
        if propuesta_id:
            propuesta = self.env['actividad.propuesta'].browse(propuesta_id)
            res['nombre_actividad'] = propuesta.actividad_id.name or ''
        return res

    def action_confirmar_aprobacion(self):
        self.ensure_one()
        if not self.creditos:
            raise ValidationError('Debe asignar los creditos a la actividad.')
        # bypass_edit_protection: el Comité asigna créditos como acción de negocio
        self.propuesta_id.actividad_id.with_context(bypass_edit_protection=True).write(
            {'creditos': self.creditos}
        )
        self.propuesta_id.action_aprobar()
        return {'type': 'ir.actions.act_window_close'}
