# -*- coding: utf-8 -*-
# Copyright 2025 Your Organization
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""
actividad_inscripcion.py
========================
Inscripción de un estudiante en una Actividad Complementaria.

Almacena:
- Referencia al estudiante (res.partner como proxy hasta tener el modelo Estudiante).
- Nivel de desempeño (0–4) asignado al finalizar la actividad.
- Observaciones del responsable.
- Estado de la constancia (generada / firmada).

Casos de uso: RA-02SC pasos 4–13 / RAE-01SC pasos 4–13.

NOTA: El campo partner_id actúa como referencia al estudiante. Cuando el
módulo de Estudiante esté disponible, reemplazar por Many2one a ese modelo
y actualizar las vistas y reglas de dominio correspondientes.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .actividad import PERFORMANCE_LEVELS


class ActividadInscripcion(models.Model):
    """Inscripción de un estudiante en una actividad complementaria."""

    _name = "actividad.inscripcion"
    _description = "Inscripción a Actividad Complementaria"
    _order = "actividad_id, partner_id"
    _rec_name = "partner_id"

    actividad_id = fields.Many2one(
        comodel_name="actividad.complementaria",
        string="Actividad",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Estudiante",
        required=True,
        ondelete="restrict",
        index=True,
        help=(
            "Referencia al estudiante. "
            "Sustituir por Many2one al modelo de Estudiante cuando esté disponible."
        ),
    )
    estado_id = fields.Many2one(
        comodel_name='actividad.estado',
        string='Estado',
        related='actividad_id.estado_id',
        store=True,
        readonly=True,
        tracking=True,
    )

    # Campos de evaluación — solo accesibles cuando la actividad está finalizada
    performance_level = fields.Selection(
        selection=PERFORMANCE_LEVELS,
        string="Nivel de Desempeño",
        tracking=True,
        help="0 = Insuficiente, 1 = Suficiente, 2 = Bueno, 3 = Notable, 4 = Excelente.",
    )
    observations = fields.Text(
        string="Observaciones",
        help="Observaciones del responsable sobre el desempeño del estudiante.",
    )

    # Constancia
    certificate_generated = fields.Boolean(
        string="Constancia Generada",
        default=False,
        readonly=True,
        copy=False,
    )
    certificate_signed = fields.Boolean(
        string="Constancia Firmada",
        default=False,
        readonly=True,
        copy=False,
    )

    # Computed helpers
    performance_label = fields.Char(
        string="Desempeño",
        compute="_compute_performance_label",
        store=True,
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    @api.depends("performance_level")
    def _compute_performance_label(self):
        level_map = dict(PERFORMANCE_LEVELS)
        for rec in self:
            rec.performance_label = (
                level_map.get(rec.performance_level, "") if rec.performance_level else ""
            )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    _sql_constraints = [
        (
            "unique_inscripcion",
            "UNIQUE(actividad_id, partner_id)",
            "El estudiante ya está inscrito en esta actividad.",
        )
    ]

    @api.constrains("performance_level")
    def _check_performance_level(self):
        """El nivel de desempeño debe estar en el rango 0–4 (enteros)."""
        valid = {lvl for lvl, _ in PERFORMANCE_LEVELS}
        for rec in self:
            if rec.performance_level and rec.performance_level not in valid:
                raise ValidationError(
                    _(
                        "El nivel de desempeño debe ser un valor entero entre 0 y 4. "
                        "Valor recibido: %s."
                    )
                    % rec.performance_level
                )

    @api.constrains("actividad_id", "partner_id")
    def _check_actividad_cupo(self):
        """No permitir inscripciones que superen el cupo máximo."""
        for rec in self:
            actividad = rec.actividad_id
            total = self.search_count(
                [("actividad_id", "=", actividad.id)]
            )
            if total > actividad.cupo_max:
                raise ValidationError(
                    _(
                        "No se puede inscribir al estudiante: "
                        "se ha alcanzado el cupo máximo de %d para la actividad '%s'."
                    )
                    % (actividad.cupo_max, actividad.name)
                )
