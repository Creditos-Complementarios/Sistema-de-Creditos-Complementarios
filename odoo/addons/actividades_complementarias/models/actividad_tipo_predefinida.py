# -*- coding: utf-8 -*-
from odoo import models, fields

# Claves de los registros fijos (predefinidos de catálogo base).
# Estos se crean desde data/tipo_predefinida_data.xml y NUNCA se tocan por código.
PREDEFINIDAS_FIJAS = ('curso_mooc', 'extraescolar')


class ActividadTipoPredefinida(models.Model):
    """
    Catálogo unificado de actividades predefinidas.

    Contiene dos tipos de registros:
    - Fijos (is_comite=False): Curso MOOC y Extraescolar, cargados por datos.
    - Generados por Comité (is_comite=True): creados automáticamente cuando el
      Comité Académico aprueba una propuesta.

    El campo `actividad_predefinida` de `actividad.complementaria` y del
    wizard apunta a este modelo en lugar del antiguo Selection estático.
    Al seleccionar cualquier registro, `tipo_actividad_id` se autocompletará
    en el formulario del JD.
    """
    _name = 'actividad.tipo.predefinida'
    _description = 'Tipo de Actividad Predefinida'
    _order = 'is_comite asc, name asc'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        size=200,
    )
    # clave técnica para los registros fijos (igual que el antiguo valor del Selection)
    key = fields.Char(
        string='Clave Técnica',
        help='Valor interno para los predefinidos de catálogo base (curso_mooc, extraescolar). '
             'Vacío para los generados por Comité.',
        index=True,
    )
    tipo_actividad_id = fields.Many2one(
        'actividad.tipo',
        string='Tipo de Actividad',
        required=True,
        ondelete='restrict',
        help='Tipo de actividad que se asignará automáticamente al seleccionar este predefinido.',
    )
    is_comite = fields.Boolean(
        string='Aprobado por Comité',
        default=False,
        help='True cuando fue generado por la aprobación de una propuesta al Comité Académico.',
    )
    actividad_origen_id = fields.Many2one(
        'actividad.complementaria',
        string='Actividad de Origen',
        readonly=True,
        ondelete='set null',
        help='Actividad aprobada por el Comité que originó este registro.',
    )
    active = fields.Boolean(default=True)
