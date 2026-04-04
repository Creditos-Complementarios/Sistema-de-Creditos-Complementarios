from odoo import models, fields


class SiiEmpleado(models.Model):
    _name = 'sii.empleado'
    _description = 'SII — CatalogoEmpleados'
    _rec_name = 'rfc_empleado'

    rfc_empleado = fields.Char(
        string='RFCEmpleado',
        required=True,
        size=20
    )
    id_departamento = fields.Many2one(
        'sii.departamento',
        string='IdDepartamento',
        required=True
    )
    nombre = fields.Char(
        string='Nombre',
        required=True
    )
    apellido_paterno = fields.Char(
        string='ApellidoPaterno',
        required=True
    )
    apellido_materno = fields.Char(
        string='ApellidoMaterno'
    )
    correo = fields.Char(
        string='Correo'
    )
    telefono = fields.Char(
        string='Telefono'
    )

    _sql_constraints = [
        ('ru', 'UNIQUE(rfc_empleado)', 'RFC único.')
    ]

    def sp_validar_empleado(self, rfc):
        e = self.search([('rfc_empleado', '=', rfc)], limit=1)
        if not e:
            return {}
        return {
            'RFCEmpleado': e.rfc_empleado,
            'Nombre': e.nombre,
            'ApellidoPaterno': e.apellido_paterno,
            'ApellidoMaterno': e.apellido_materno or '',
            'IdDepartamento': e.id_departamento.id,
            'Correo': e.correo or '',
        }
