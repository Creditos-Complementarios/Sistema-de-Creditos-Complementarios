# -*- coding: utf-8 -*-
from odoo import models, fields


class EstadoActividad(models.Model):
    _name = 'actividad.estado'
    _description = 'Estado de Actividad Complementaria'
    _order = 'sequence'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Selection([
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('pendiente_inicio', 'Pendiente de Inicio'),
        ('en_curso', 'En Curso'),
        ('finalizada', 'Finalizada'),
    ], string='Código', required=True)
    sequence = fields.Integer(default=10)
