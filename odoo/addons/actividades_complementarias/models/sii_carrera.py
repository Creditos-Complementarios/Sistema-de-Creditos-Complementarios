from odoo import models, fields


class SiiCarrera(models.Model):
    _name = 'sii.carrera'
    _description = 'SII — Carrera'
    _rec_name = 'nombre'

    clave_carrera = fields.Char(
        string='ClaveCarrera',
        required=True,
        size=10
    )
    nombre = fields.Char(
        string='Nombre',
        required=True
    )
    reticula = fields.Char(
        string='Reticula',
        required=True
    )

    _sql_constraints = [
        ('cu', 'UNIQUE(clave_carrera)', 'ClaveCarrera única.')
    ]
