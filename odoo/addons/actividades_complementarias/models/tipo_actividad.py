# -*- coding: utf-8 -*-
from odoo import models, fields


class TipoActividad(models.Model):
    _name = 'actividad.tipo'
    _description = 'Tipo de Actividad Complementaria'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        size=200,
    )
    es_predefinida = fields.Boolean(
        string='Es predefinida',
        default=False,
        help='Las actividades predefinidas no requieren aprobación del Comité Académico.',
    )
    active = fields.Boolean(default=True)
