# -*- coding: utf-8 -*-
from odoo import models, fields


class ActividadPredefinidaComite(models.Model):
    """
    Catálogo de actividades aprobadas por el Comité Académico.
    Solo se registran aquí las actividades que pasaron por el flujo
    de propuesta al comité y fueron aprobadas (no rechazadas, no predefinidas
    directas al catálogo).
    """
    _name = 'actividad.predefinida.comite'
    _description = 'Actividad Predefinida por Comité Académico'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre de la Actividad',
        required=True,
        size=200,
    )
    tipo_actividad_id = fields.Many2one(
        'actividad.tipo',
        string='Tipo de Actividad',
        required=True,
        ondelete='restrict',
        help='Tipo de actividad que tenía la actividad cuando fue aprobada por el Comité.',
    )
    actividad_origen_id = fields.Many2one(
        'actividad.complementaria',
        string='Actividad de Origen',
        readonly=True,
        ondelete='set null',
        help='Actividad original aprobada por el Comité que originó este predefinido.',
    )
    active = fields.Boolean(default=True)
