from odoo import models, fields


class SiiTipoUsuario(models.Model):
    _name = 'sii.tipousuario'
    _description = 'SII — TipoUsuario'
    _rec_name = 'nombre'

    nombre = fields.Char(
        string='Nombre',
        required=True
    )
