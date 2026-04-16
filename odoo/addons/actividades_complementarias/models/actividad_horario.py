# -*- coding: utf-8 -*-
# Copyright 2025 Your Organization
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""
actividad_horario.py
====================
Horario por día de una Actividad Complementaria.

Validación (regla de negocio RA-01SC):
- hora_fin > hora_inicio
- hora_fin < 23:00 (expresado como 23.0 en formato float)
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

WEEKDAYS = [
    ("0", "Lunes"),
    ("1", "Martes"),
    ("2", "Miércoles"),
    ("3", "Jueves"),
    ("4", "Viernes"),
    ("5", "Sábado"),
    ("6", "Domingo"),
]


class ActividadHorario(models.Model):
    """Bloque de horario asociado a un día de la semana para una actividad."""

    _name = "actividad.horario"
    _description = "Horario por Día de Actividad Complementaria"
    _order = "dia_semana, hora_inicio"
    _rec_name = "display_name"

    actividad_id = fields.Many2one(
        comodel_name="actividad.complementaria",
        string="Actividad",
        required=True,
        ondelete="cascade",
        index=True,
    )
    dia_semana = fields.Selection(
        selection=WEEKDAYS,
        string="Día de la Semana",
        required=True,
    )
    hora_inicio = fields.Float(
        string="Hora de Inicio",
        required=True,
        digits=(2, 2),
        help="Formato 24 h (ej. 8.5 = 08:30).",
    )
    hora_fin = fields.Float(
        string="Hora de Fin",
        required=True,
        digits=(2, 2),
        help="Formato 24 h. Debe ser menor a 23:00 y mayor a la hora de inicio.",
    )
    display_name = fields.Char(
        string="Descripción",
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("dia_semana", "hora_inicio", "hora_fin")
    def _compute_display_name(self):
        day_labels = dict(WEEKDAYS)
        for rec in self:
            if rec.dia_semana:
                rec.display_name = "%s %s–%s" % (
                    day_labels.get(rec.dia_semana, ""),
                    self._float_to_time(rec.hora_inicio),
                    self._float_to_time(rec.hora_fin),
                )
            else:
                rec.display_name = ""

    @api.constrains("hora_inicio", "hora_fin")
    def _check_horario(self):
        """hora_fin > hora_inicio y hora_fin < 23:00."""
        for rec in self:
            if rec.hora_fin <= rec.hora_inicio:
                raise ValidationError(
                    _("La hora de fin debe ser mayor a la hora de inicio.")
                )
            if rec.hora_fin >= 23.0:
                raise ValidationError(
                    _("La hora de fin debe ser menor a las 23:00.")
                )
            if rec.hora_inicio < 0:
                raise ValidationError(
                    _("La hora de inicio no puede ser negativa.")
                )

    @staticmethod
    def _float_to_time(value):
        """Convierte un float de hora a formato 'HH:MM'."""
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return "%02d:%02d" % (hours, minutes)
