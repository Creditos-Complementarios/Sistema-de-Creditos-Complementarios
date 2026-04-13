from odoo import models, fields


class SiiPeriodo(models.Model):
    _name = 'sii.periodo'
    _description = 'SII — Periodo'
    _rec_name = 'clave_periodo'
    _order = 'fecha_inicio desc'

    clave_periodo = fields.Char(
        string='ClavePeriodo',
        required=True,
        size=10
    )
    fecha_inicio = fields.Date(
        string='FechaInicio',
        required=True
    )
    fecha_fin = fields.Date(
        string='FechaFin',
        required=True
    )

    _sql_constraints = [
        ('cu', 'UNIQUE(clave_periodo)', 'ClavePeriodo única.')
    ]
    