# -*- coding: utf-8 -*-
# Copyright 2025 Your Organization
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""
actividad_asistencia.py
=======================
Registro de asistencia por estudiante y fecha para una Actividad Complementaria.

Reglas de negocio (RA-02SC / RAE-01SC):
- Solo se puede registrar asistencia dentro del rango de fechas de la actividad.
- El pase de lista no puede modificarse una vez finalizada la actividad.
- Un mismo estudiante no puede tener dos registros en la misma fecha para la
  misma actividad (restricción SQL).
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ActividadAsistencia(models.Model):
    """Registro de asistencia de un estudiante en una sesión de la actividad."""

    _name = "actividad.asistencia"
    _description = "Asistencia a Actividad Complementaria"
    _order = "actividad_id, fecha, partner_id"

    actividad_id = fields.Many2one(
        comodel_name="actividad.complementaria",
        string="Actividad",
        required=True,
        ondelete="cascade",
        index=True,
    )
    inscripcion_id = fields.Many2one(
        comodel_name="actividad.inscripcion",
        string="Inscripción",
        required=True,
        ondelete="cascade",
        index=True,
        help="Inscripción del estudiante en la actividad.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Estudiante",
        related="inscripcion_id.partner_id",
        store=True,
        readonly=True,
    )
    fecha = fields.Date(
        string="Fecha",
        required=True,
        default=fields.Date.today,
    )
    presente = fields.Boolean(
        string="Presente",
        default=False,
    )

    # ------------------------------------------------------------------
    # SQL Constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_asistencia",
            "UNIQUE(actividad_id, inscripcion_id, fecha)",
            "Ya existe un registro de asistencia para este estudiante en esa fecha.",
        )
    ]

    # ------------------------------------------------------------------
    # Constraints de negocio
    # ------------------------------------------------------------------

    @api.constrains("fecha", "actividad_id")
    def _check_fecha_dentro_rango(self):
        """La fecha del pase de lista debe estar dentro del rango de la actividad."""
        for rec in self:
            actividad = rec.actividad_id
            if not actividad.date_start or not actividad.date_end:
                continue
            if rec.fecha < actividad.date_start or rec.fecha > actividad.date_end:
                raise ValidationError(
                    _(
                        "La fecha de asistencia (%s) está fuera del rango de la "
                        "actividad (%s – %s)."
                    )
                    % (rec.fecha, actividad.date_start, actividad.date_end)
                )

    @api.constrains("actividad_id")
    def _check_actividad_no_finalizada(self):
        """No se puede modificar el pase de lista de una actividad finalizada."""
        for rec in self:
            if rec.actividad_id.state == "done":
                raise ValidationError(
                    _(
                        "El pase de lista no puede modificarse una vez que "
                        "la actividad ha finalizado."
                    )
                )

    # ------------------------------------------------------------------
    # Override write
    # ------------------------------------------------------------------

    def write(self, vals):
        """Bloquea cualquier modificación si la actividad ya está finalizada."""
        for rec in self:
            if rec.actividad_id.state == "done":
                raise ValidationError(
                    _(
                        "No se puede modificar el registro de asistencia: "
                        "la actividad '%s' ya está finalizada."
                    )
                    % rec.actividad_id.name
                )
        return super().write(vals)
