# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class PropuestaActividadComplementaria(models.Model):
    _name = 'actividad.propuesta'
    _description = 'Propuesta de Actividad Complementaria al Comité'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc'

    # ── Datos básicos ────────────────────────────────────────────────────────
    actividad_id = fields.Many2one(
        'actividad.complementaria',
        string='Actividad',
        required=True,
        ondelete='cascade',
    )
    encabezado = fields.Char(
        string='Encabezado',
        compute='_compute_encabezado',
        store=True,
    )
    fecha = fields.Date(
        string='Fecha de Envío',
        default=fields.Date.today,
        readonly=True,
    )
    fecha_limite_revision = fields.Date(
        string='Fecha Límite de Revisión',
        compute='_compute_fecha_limite',
        store=True,
        help='La propuesta se aprueba automáticamente si no hay respuesta en 5 días hábiles.',
    )

    # ── Estado ───────────────────────────────────────────────────────────────
    estado_solicitud_id = fields.Many2one(
        'actividad.estado.solicitud',
        string='Estado',
        tracking=True,
    )
    estado_code = fields.Selection(
        related='estado_solicitud_id.code',
        string='Código de Estado',
        store=True,
        readonly=True,
    )
    motivo_rechazo = fields.Text(string='Motivo de Rechazo')

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    @api.depends('actividad_id')
    def _compute_encabezado(self):
        for rec in self:
            rec.encabezado = rec.actividad_id.name if rec.actividad_id else ''

    @api.depends('fecha')
    def _compute_fecha_limite(self):
        for rec in self:
            if rec.fecha:
                rec.fecha_limite_revision = rec.fecha + timedelta(days=5)
            else:
                rec.fecha_limite_revision = False

    # ────────────────────────────────────────────────────────────────────────
    # Business logic
    # ────────────────────────────────────────────────────────────────────────

    def action_aprobar(self):
        self.ensure_one()
        estado_aprobada = self.env.ref('actividades_complementarias.estado_solicitud_aprobada')
        estado_act_aprobada = self.env.ref('actividades_complementarias.estado_aprobada')
        self.write({'estado_solicitud_id': estado_aprobada.id})
        self.actividad_id.write({'estado_id': estado_act_aprobada.id})
        self.message_post(body='Propuesta aprobada por el Comité Académico.')

    def action_rechazar(self):
        self.ensure_one()
        if not self.motivo_rechazo:
            raise ValidationError('Debe indicar el motivo de rechazo.')
        estado_rechazada = self.env.ref('actividades_complementarias.estado_solicitud_rechazada')
        estado_act_rechazada = self.env.ref('actividades_complementarias.estado_rechazada')
        self.write({'estado_solicitud_id': estado_rechazada.id})
        self.actividad_id.write({'estado_id': estado_act_rechazada.id})
        self.message_post(body=f'Propuesta rechazada. Motivo: {self.motivo_rechazo}')

    def _auto_aprobar_propuestas_vencidas(self):
        """Cron: aprueba automáticamente propuestas sin respuesta tras 5 días."""
        hoy = date.today()
        estado_en_revision = self.env.ref('actividades_complementarias.estado_solicitud_en_revision')
        propuestas_vencidas = self.search([
            ('estado_solicitud_id', '=', estado_en_revision.id),
            ('fecha_limite_revision', '<', hoy),
        ])
        for propuesta in propuestas_vencidas:
            propuesta.action_aprobar()
            propuesta.message_post(body='Aprobada automáticamente por vencimiento de plazo (5 días).')
