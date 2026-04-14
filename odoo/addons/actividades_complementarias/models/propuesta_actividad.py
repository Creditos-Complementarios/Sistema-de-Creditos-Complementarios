# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class PropuestaActividadComplementaria(models.Model):
    _name = 'actividad.propuesta'
    _description = 'Propuesta de Actividad Complementaria al Comité'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha desc'
    _rec_name = 'encabezado'

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
        default=lambda self: fields.Date.context_today(self),
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

    # ── Campos de la actividad para lectura del Comité ───────────────────
    actividad_nombre = fields.Char(related='actividad_id.name', string='Nombre', readonly=True)
    actividad_tipo = fields.Many2one(related='actividad_id.tipo_actividad_id', string='Tipo', readonly=True)
    actividad_jefe = fields.Many2one(related='actividad_id.jefe_departamento_id', string='Jefe', readonly=True)
    actividad_departamento = fields.Many2one(
        related='actividad_id.departamento_id',
        string='Departamento',
        readonly=True,
    )
    actividad_periodo = fields.Many2one(related='actividad_id.periodo', string='Periodo', readonly=True)
    actividad_fecha_inicio = fields.Date(related='actividad_id.fecha_inicio', string='Fecha Inicio', readonly=True)
    actividad_fecha_fin = fields.Date(related='actividad_id.fecha_fin', string='Fecha Fin', readonly=True)
    actividad_horas = fields.Float(related='actividad_id.cantidad_horas', string='Horas', readonly=True)
    actividad_creditos = fields.Selection(related='actividad_id.creditos', string='Créditos', readonly=True)
    actividad_descripcion = fields.Text(related='actividad_id.descripcion', string='Descripción', readonly=True)
    actividad_cupo = fields.Char(
        string='Cupo',
        compute='_compute_actividad_cupo',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    @api.depends('actividad_id')
    def _compute_encabezado(self):
        for rec in self:
            rec.encabezado = rec.actividad_id.name if rec.actividad_id else ''

    @api.depends('actividad_id')
    def _compute_actividad_cupo(self):
        for rec in self:
            if rec.actividad_id:
                if rec.actividad_id.cupo_ilimitado:
                    rec.actividad_cupo = 'Ilimitado'
                else:
                    rec.actividad_cupo = f'{rec.actividad_id.cupo_min} – {rec.actividad_id.cupo_max}'
            else:
                rec.actividad_cupo = ''

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
        self.sudo().write({'estado_solicitud_id': estado_aprobada.id})
        self.actividad_id.sudo().with_context(bypass_edit_protection=True).write(
            {'estado_id': estado_act_aprobada.id}
        )
        # ── Registrar en el catálogo de predefinidas por Comité ──────────────
        # Solo se ejecuta desde este flujo (propuesta enviada al comité y aprobada).
        # Rechazos nunca llegan aquí. Actividades predefinidas directas al catálogo
        # nunca generan una propuesta, por lo que tampoco llegan aquí.
        actividad = self.actividad_id
        if actividad and actividad.tipo_actividad_id:
            Predefinida = self.env['actividad.tipo.predefinida'].sudo()
            existente = Predefinida.search([('name', '=', actividad.name), ('is_comite', '=', True)], limit=1)
            if not existente:
                Predefinida.create({
                    'name': actividad.name,
                    'tipo_actividad_id': actividad.tipo_actividad_id.id,
                    'is_comite': True,
                    'actividad_origen_id': actividad.id,
                })
        self.message_post(body='Propuesta aprobada por el Comité Académico.')

    def action_rechazar(self):
        self.ensure_one()
        if not self.motivo_rechazo:
            raise ValidationError('Debe indicar el motivo de rechazo.')
        estado_rechazada = self.env.ref('actividades_complementarias.estado_solicitud_rechazada')
        estado_act_rechazada = self.env.ref('actividades_complementarias.estado_rechazada')
        self.sudo().write({'estado_solicitud_id': estado_rechazada.id})
        self.actividad_id.sudo().with_context(bypass_edit_protection=True).write(
            {'estado_id': estado_act_rechazada.id}
        )
        self.message_post(body=f'Propuesta rechazada. Motivo: {self.motivo_rechazo}')

    def action_abrir_wizard_rechazo(self):
        """Abre el wizard de rechazo para capturar el motivo."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rechazar Propuesta',
            'res_model': 'actividad.wizard.rechazar',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_propuesta_id': self.id},
        }

    def action_abrir_wizard_aprobacion(self):
        """Abre el wizard de aprobacion para asignar creditos."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aprobar Propuesta',
            'res_model': 'actividad.wizard.aprobar',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_propuesta_id': self.id},
        }

    def action_regresar_lista(self):
        """Regresa a la lista segun el contexto de origen."""
        ctx = self.env.context
        origen = ctx.get('origen_propuesta', 'todas')
        if origen == 'pendientes':
            action_ref = self.env.ref(
                'actividades_complementarias.action_propuesta_pendiente',
                raise_if_not_found=False,
            )
        elif origen == 'mis_propuestas':
            action_ref = self.env.ref(
                'actividades_complementarias.action_propuesta',
                raise_if_not_found=False,
            )
        else:
            action_ref = self.env.ref(
                'actividades_complementarias.action_propuesta_todas',
                raise_if_not_found=False,
            )
        if action_ref:
            action = action_ref.sudo().read()[0]
            action['target'] = 'current'
            return action
        return {
            'type': 'ir.actions.act_window',
            'name': 'Propuestas',
            'res_model': 'actividad.propuesta',
            'view_mode': 'list,form',
            'target': 'current',
        }

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
