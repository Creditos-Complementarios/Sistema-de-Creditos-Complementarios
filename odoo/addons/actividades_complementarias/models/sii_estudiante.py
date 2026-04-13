from odoo import models, fields


class SiiEstudiante(models.Model):
    _name = 'sii.estudiante'
    _description = 'SII — Estudiante'
    _rec_name = 'no_control'

    no_control = fields.Char(
        string='NoControl',
        required=True,
        size=20
    )
    id_carrera = fields.Many2one(
        'sii.carrera',
        string='IdCarrera',
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
    semestre = fields.Integer(
        string='Semestre'
    )
    grupo = fields.Char(
        string='Grupo',
        size=5
    )
    estado_liberacion = fields.Char(
        string='EstadoLiberacion'
    )
    estado_estudiante = fields.Char(
        string='EstadoEstudiante'
    )
    correo = fields.Char(
        string='Correo'
    )
    telefono = fields.Char(
        string='Telefono'
    )

    _sql_constraints = [
        ('nu', 'UNIQUE(no_control)', 'NoControl único.')
    ]

    def sp_validar_alumno(self, nc):
        e = self.search([('no_control', '=', nc)], limit=1)
        if not e:
            return {}
        return {
            'NoControl': e.no_control,
            'Nombre': e.nombre,
            'ApellidoPaterno': e.apellido_paterno,
            'ApellidoMaterno': e.apellido_materno or '',
            'IdCarrera': e.id_carrera.clave_carrera,
            'Semestre': e.semestre,
            'Grupo': e.grupo or '',
            'EstadoEstudiante': e.estado_estudiante or '',
            'Correo': e.correo or '',
        }

    def sp_alumnos_por_carreras(self, carreras):
        es = self.search([('id_carrera.clave_carrera', 'in', carreras)])
        return [
            {
                'NoControl': e.no_control,
                'Nombre': e.nombre,
                'ApellidoPaterno': e.apellido_paterno,
                'IdCarrera': e.id_carrera.clave_carrera,
                'Correo': e.correo or '',
            }
            for e in es
        ]
