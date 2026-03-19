# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class WizardNuevaActividad(models.TransientModel):
    """
    Wizard JD-01SC: Solicitud de nuevo tipo de actividad complementaria.
    Guía al JD para registrar una actividad y decide automáticamente
    si se envía al catálogo (predefinida) o al Comité Académico (nueva).
    """
    _name = 'actividad.wizard.nueva'
    _description = 'Wizard: Generar Actividad Complementaria'

    # ── Datos obligatorios ────────────────────────────────────────────────
    name = fields.Char(string='Nombre de la Actividad', required=True, size=200)
    descripcion = fields.Text(string='Descripción', size=2000)
    tipo_actividad_id = fields.Many2one(
        'actividad.tipo', string='Tipo de Actividad', required=True
    )
    periodo = fields.Char(string='Periodo Escolar', required=True)
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de Finalización', required=True)
    cantidad_horas = fields.Float(string='Cantidad de Horas', required=True)
    horario = fields.Text(string='Horario por Día (si aplica)')
    cupo_ilimitado = fields.Boolean(string='Cupo Ilimitado', default=False)
    cupo_min = fields.Integer(string='Cupo Mínimo', default=1)
    cupo_max = fields.Integer(string='Cupo Máximo', default=30)
    ruta_imagen = fields.Image(string='Imagen Alusiva', max_width=1024, max_height=1024)

    # ── Datos condicionales (solo si predefinida) ─────────────────────────
    es_predefinida = fields.Boolean(
        string='Tipo Predefinido',
        compute='_compute_es_predefinida',
        store=False,
    )
    responsable_actividad_id = fields.Many2one(
        'res.users', string='Responsable de Actividad'
    )
    creditos = fields.Integer(string='Cantidad de Créditos')

    # ────────────────────────────────────────────────────────────────────────
    @api.depends('tipo_actividad_id')
    def _compute_es_predefinida(self):
        for rec in self:
            rec.es_predefinida = rec.tipo_actividad_id.es_predefinida if rec.tipo_actividad_id else False

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_inicio and rec.fecha_inicio < date.today():
                raise ValidationError('La fecha de inicio no puede ser anterior a hoy.')
            if rec.fecha_fin and rec.fecha_inicio and rec.fecha_fin <= rec.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for rec in self:
            if not rec.cupo_ilimitado:
                if rec.cupo_min < 1:
                    raise ValidationError('El cupo mínimo debe ser al menos 1.')
                if rec.cupo_max < rec.cupo_min:
                    raise ValidationError('El cupo máximo debe ser mayor o igual al cupo mínimo.')

    # ────────────────────────────────────────────────────────────────────────
    # Actions
    # ────────────────────────────────────────────────────────────────────────

    def action_confirmar(self):
        """
        Crea la actividad y la enruta:
        - Predefinida → catálogo directamente con estado 'pendiente_inicio'.
        - Nueva       → propuesta al Comité con estado 'en_revision'.
        """
        self.ensure_one()

        es_predefinida = self.tipo_actividad_id.es_predefinida

        if es_predefinida:
            estado = self.env.ref('actividades_complementarias.estado_pendiente_inicio')
        else:
            # Las nuevas quedan como aprobadas al crearse para el flujo de propuesta
            estado = self.env.ref('actividades_complementarias.estado_aprobada')

        vals = {
            'name': self.name,
            'descripcion': self.descripcion,
            'tipo_actividad_id': self.tipo_actividad_id.id,
            'periodo': self.periodo,
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'cantidad_horas': self.cantidad_horas,
            'horario': self.horario,
            'cupo_ilimitado': self.cupo_ilimitado,
            'cupo_min': self.cupo_min,
            'cupo_max': self.cupo_max,
            'ruta_imagen': self.ruta_imagen,
            'jefe_departamento_id': self.env.user.id,
            'estado_id': estado.id,
        }

        if es_predefinida:
            vals['responsable_actividad_id'] = self.responsable_actividad_id.id if self.responsable_actividad_id else False
            vals['creditos'] = self.creditos
            vals['en_catalogo'] = False  # JD decide luego cuándo publicar

        actividad = self.env['actividad.complementaria'].create(vals)

        if not es_predefinida:
            # Crear propuesta al comité
            estado_revision = self.env.ref('actividades_complementarias.estado_solicitud_en_revision')
            self.env['actividad.propuesta'].create({
                'actividad_id': actividad.id,
                'estado_solicitud_id': estado_revision.id,
            })
            actividad.message_post(
                body='Propuesta enviada al Comité Académico para su revisión.'
            )

        # Abrir el registro recién creado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'actividad.complementaria',
            'res_id': actividad.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancelar(self):
        return {'type': 'ir.actions.act_window_close'}
