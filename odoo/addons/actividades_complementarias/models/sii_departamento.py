from odoo import models, fields


class SiiDepartamento(models.Model):
    _name = 'sii.departamento'
    _description = 'SII — catalogoDepartamentos'
    _rec_name = 'nombre_departamento'

    nombre_departamento = fields.Char(
        string='nombreDepartamento',
        required=True
    )
