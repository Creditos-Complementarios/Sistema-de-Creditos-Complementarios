# -*- coding: utf-8 -*-
from odoo import models, fields


class EstadoSolicitud(models.Model):
    _name = 'actividad.estado.solicitud'
    _description = 'Estado de Propuesta/Solicitud'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Selection([
        ('en_revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ], string='Código', required=True)
