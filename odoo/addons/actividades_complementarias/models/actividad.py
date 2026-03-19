# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class Actividad(models.Model):
    _name = 'actividad.complementaria'
    _description = 'Actividad Complementaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc'

    # ── Identificación ──────────────────────────────────────────────────────
    name = fields.Char(
        string='Nombre de la Actividad',
        required=True,
        size=200,
        tracking=True,
    )
    descripcion = fields.Text(
        string='Descripción',
        size=2000,
    )
    tipo_actividad_id = fields.Many2one(
        'actividad.tipo',
        string='Tipo de Actividad',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    periodo = fields.Char(
        string='Periodo Escolar',
        required=True,
        help='Ej: 2025-A',
    )

    # ── Responsables ────────────────────────────────────────────────────────
    jefe_departamento_id = fields.Many2one(
        'res.users',
        string='Jefe de Departamento',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    responsable_actividad_id = fields.Many2one(
        'res.users',
        string='Responsable de Actividad',
        tracking=True,
        help='Debe ser un profesor registrado en el mismo departamento.',
    )
    departamento_id = fields.Many2one(
        'actividad.departamento',
        string='Departamento',
        compute='_compute_departamento',
        store=True,
        readonly=True,
    )

    # ── Fechas y duración ───────────────────────────────────────────────────
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True, tracking=True)
    fecha_fin = fields.Date(string='Fecha de Finalización', required=True, tracking=True)
    cantidad_horas = fields.Float(string='Cantidad de Horas', required=True)
    creditos = fields.Integer(string='Cantidad de Créditos')
    horario = fields.Text(string='Horario por Día (si aplica)')

    # ── Cupos ────────────────────────────────────────────────────────────────
    cupo_min = fields.Integer(string='Cupo Mínimo', default=1)
    cupo_max = fields.Integer(string='Cupo Máximo', default=30)
    cupo_ilimitado = fields.Boolean(string='Cupo Ilimitado', default=False)

    # ── Imagen y multimedia ─────────────────────────────────────────────────
    ruta_imagen = fields.Image(string='Imagen Alusiva', max_width=1024, max_height=1024)

    # ── Estado ───────────────────────────────────────────────────────────────
    estado_id = fields.Many2one(
        'actividad.estado',
        string='Estado',
        tracking=True,
    )
    estado_code = fields.Selection(
        related='estado_id.code',
        string='Código de Estado',
        store=True,
        readonly=True,
    )

    # ── Alumnos asignados ────────────────────────────────────────────────────
    alumno_ids = fields.Many2many(
        'res.partner',
        'actividad_alumno_rel',
        'actividad_id',
        'alumno_id',
        string='Alumnos Asignados',
    )
    alumno_count = fields.Integer(
        string='# Alumnos',
        compute='_compute_alumno_count',
    )

    # ── Flags de control ─────────────────────────────────────────────────────
    en_catalogo = fields.Boolean(string='En Catálogo', default=False, tracking=True)
    constancias_firmadas = fields.Boolean(string='Constancias Firmadas', default=False)

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    @api.depends('jefe_departamento_id')
    def _compute_departamento(self):
        """Asigna automáticamente el departamento del JD."""
        for rec in self:
            emp = self.env['actividad.empleado.permiso'].search(
                [('user_id', '=', rec.jefe_departamento_id.id)], limit=1
            )
            rec.departamento_id = emp.departamento_id if emp else False

    @api.depends('alumno_ids')
    def _compute_alumno_count(self):
        for rec in self:
            rec.alumno_count = len(rec.alumno_ids)

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

    @api.constrains('name', 'periodo')
    def _check_nombre_unico_periodo(self):
        for rec in self:
            domain = [
                ('name', '=ilike', rec.name),
                ('periodo', '=', rec.periodo),
                ('id', '!=', rec.id),
                ('estado_code', 'not in', ['rechazada', 'finalizada']),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    f'Ya existe una actividad activa con el nombre "{rec.name}" en el periodo {rec.periodo}.'
                )

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for rec in self:
            if not rec.cupo_ilimitado:
                if rec.cupo_min < 1:
                    raise ValidationError('El cupo mínimo debe ser al menos 1.')
                if rec.cupo_max < rec.cupo_min:
                    raise ValidationError('El cupo máximo debe ser mayor o igual al cupo mínimo.')

    # ────────────────────────────────────────────────────────────────────────
    # Business Logic
    # ────────────────────────────────────────────────────────────────────────

    def action_enviar_catalogo(self):
        """Envía la actividad aprobada al catálogo."""
        self.ensure_one()
        if self.estado_code not in ('aprobada', 'pendiente_inicio'):
            raise ValidationError('Solo se pueden enviar al catálogo actividades aprobadas o pendientes de inicio.')
        self.write({'en_catalogo': True})
        self.message_post(body='Actividad enviada al catálogo.')

    def action_firmar_constancias(self):
        """Replica la firma del JD a todas las constancias de la actividad."""
        self.ensure_one()
        if self.estado_code != 'finalizada':
            raise ValidationError('Solo se pueden firmar constancias de actividades finalizadas.')
        self.write({'constancias_firmadas': True})
        self.message_post(body='Constancias firmadas por el Jefe de Departamento.')

    def _actualizar_estado_por_fecha(self):
        """Cron: actualiza estados según fechas."""
        hoy = date.today()
        estado_en_curso = self.env.ref('actividades_complementarias.estado_en_curso', raise_if_not_found=False)
        estado_finalizada = self.env.ref('actividades_complementarias.estado_finalizada', raise_if_not_found=False)

        if estado_en_curso:
            pendientes = self.search([
                ('estado_code', '=', 'pendiente_inicio'),
                ('fecha_inicio', '<=', hoy),
            ])
            pendientes.write({'estado_id': estado_en_curso.id})

        if estado_finalizada:
            en_curso = self.search([
                ('estado_code', '=', 'en_curso'),
                ('fecha_fin', '<=', hoy),
            ])
            en_curso.write({'estado_id': estado_finalizada.id})


class ActividadDepartamento(models.Model):
    """Catálogo simple de departamentos para asociar JD y personal."""
    _name = 'actividad.departamento'
    _description = 'Departamento'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    jefe_id = fields.Many2one('res.users', string='Jefe de Departamento')
