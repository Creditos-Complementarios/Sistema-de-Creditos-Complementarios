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
    periodo = fields.Many2one(
        'actividad.periodo',
        string='Periodo Escolar',
        required=True,
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
        help='Solo usuarios del grupo Responsable de Actividad.',
    )
    dominio_responsable = fields.Binary(
        compute='_compute_dominios',
        string='Dominio Responsable',
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
    creditos = fields.Selection([
        ('0.5', '0.5 créditos'),
        ('1.0', '1 crédito'),
        ('1.5', '1.5 créditos'),
        ('2.0', '2 créditos'),
    ], string='Cantidad de Créditos')
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
        'res.users',
        'actividad_alumno_rel',
        'actividad_id',
        'alumno_id',
        string='Alumnos Asignados',
    )
    dominio_alumnos = fields.Binary(
        compute='_compute_dominios',
        string='Dominio Alumnos',
    )
    alumno_count = fields.Integer(
        string='# Alumnos',
        compute='_compute_alumno_count',
    )

    # ── Flags de control ─────────────────────────────────────────────────────
    en_catalogo = fields.Boolean(string='En Catálogo', default=False, tracking=True)
    constancias_firmadas = fields.Boolean(string='Constancias Firmadas', default=False)
    tiene_propuesta_activa = fields.Boolean(
        string='Tiene Propuesta Activa',
        compute='_compute_tiene_propuesta_activa',
        help='True si ya existe una propuesta en revisión o aprobada.',
    )
    tipo_actividad_predefinida = fields.Boolean(
        related='tipo_actividad_id.es_predefinida',
        string='Tipo Predefinido',
        store=False,
    )
    tipo_es_nueva = fields.Boolean(
        compute='_compute_tipo_es_nueva',
        string='Tipo es Nueva Propuesta',
        store=False,
    )
    actividad_predefinida = fields.Selection([
        ('curso_mooc', 'Curso MOOC'),
        ('extraescolar', 'Extraescolar'),
    ], string='Actividades Predefinidas',
       tracking=True,
       help='Si la actividad es de tipo predefinido se aprueba automáticamente '
            'sin pasar por el Comité Académico. Puede dejarse en blanco para quitarlo.',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Computes
    # ────────────────────────────────────────────────────────────────────────

    @api.depends('tipo_actividad_id')
    def _compute_tipo_es_nueva(self):
        """True cuando el tipo de actividad es 'Nueva (Propuesta)',
        para ocultar el campo Actividades Predefinidas en ese caso."""
        for rec in self:
            rec.tipo_es_nueva = (
                rec.tipo_actividad_id and
                rec.tipo_actividad_id.name == 'Nueva (Propuesta)'
            )

    def _compute_dominios(self):
        """
        Computa dominios para responsable y alumnos.
        En Odoo 19 'groups_id' no es buscable en res.users via dominio ORM,
        por lo que usamos SQL para obtener los user IDs del grupo.
        """
        def _user_ids_en_grupo(xmlid):
            grupo = self.env.ref(xmlid, raise_if_not_found=False)
            if not grupo:
                return []
            self.env.cr.execute(
                """SELECT uid FROM res_groups_users_rel WHERE gid = %s""",
                (grupo.id,)
            )
            return [r[0] for r in self.env.cr.fetchall()]

        ids_responsable = _user_ids_en_grupo('actividades_complementarias.group_responsable_actividad')
        ids_alumno = _user_ids_en_grupo('actividades_complementarias.group_alumno')

        dom_resp = [('id', 'in', ids_responsable)] if ids_responsable else [('id', '=', False)]
        dom_alum = [('id', 'in', ids_alumno)] if ids_alumno else [('id', '=', False)]
        for rec in self:
            rec.dominio_responsable = dom_resp
            rec.dominio_alumnos = dom_alum

    def _compute_tiene_propuesta_activa(self):
        for rec in self:
            rec.tiene_propuesta_activa = bool(
                self.env['actividad.propuesta'].search_count([
                    ('actividad_id', '=', rec.id),
                    ('estado_code', 'in', ('en_revision', 'aprobada')),
                ])
            )

    @api.depends('jefe_departamento_id')
    def _compute_departamento(self):
        """Asigna automáticamente el departamento del JD buscando en actividad.departamento."""
        for rec in self:
            if not rec.jefe_departamento_id:
                rec.departamento_id = False
                continue
            # Primero buscar en el catálogo de departamentos (jefe_id)
            depto = self.env['actividad.departamento'].search(
                [('jefe_id', '=', rec.jefe_departamento_id.id)], limit=1
            )
            if depto:
                rec.departamento_id = depto
            else:
                # Fallback: buscar en el registro de permisos del empleado
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
            # No validar fechas pasadas cuando se cargan datos de demo o desde el sistema
            if not self.env.context.get('install_demo') and not self.env.context.get('skip_fecha_check'):
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

    def action_enviar_comite(self):
        """Envía la actividad como propuesta al Comité Académico."""
        self.ensure_one()
        if self.estado_code in ('aprobada', 'pendiente_inicio', 'en_curso', 'finalizada'):
            raise ValidationError(
                'Esta actividad ya fue aprobada o está en curso/finalizada. '
                'No puede ser reenviada al Comité Académico.'
            )
        # Verificar que no haya propuesta pendiente o aprobada ya
        propuesta_existente = self.env['actividad.propuesta'].search([
            ('actividad_id', '=', self.id),
            ('estado_code', 'in', ('en_revision', 'aprobada')),
        ], limit=1)
        if propuesta_existente:
            raise ValidationError('Esta actividad ya tiene una propuesta activa o aprobada en el Comité.')
        estado_revision_solicitud = self.env.ref('actividades_complementarias.estado_solicitud_en_revision')
        estado_en_revision = self.env.ref('actividades_complementarias.estado_en_revision')
        self.write({'estado_id': estado_en_revision.id})
        self.env['actividad.propuesta'].create({
            'actividad_id': self.id,
            'estado_solicitud_id': estado_revision_solicitud.id,
        })
        self.message_post(
            body='Propuesta enviada al Comité Académico para su revisión. '
                 'Se aprobará automáticamente si no hay respuesta en 5 días.'
        )
        # Abrir la lista de propuestas
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mis Propuestas al Comité',
            'res_model': 'actividad.propuesta',
            'view_mode': 'list,form',
            'domain': [('actividad_id', '=', self.id)],
            'target': 'current',
        }

    def action_enviar_catalogo(self):
        """Envía la actividad al catálogo.
        Si tiene actividad_predefinida, se aprueba automáticamente antes de enviar.
        """
        self.ensure_one()
        if self.estado_code == 'rechazada':
            raise ValidationError(
                'Las actividades rechazadas no pueden ser enviadas al catálogo.'
            )
        if self.estado_code == 'finalizada':
            raise ValidationError(
                'Esta actividad ya fue finalizada y no puede ser enviada al catálogo. '
                'Cree una nueva propuesta de actividad si desea volver a ofertarla.'
            )
        # Si es predefinida y aún no está en un estado válido, la aprobamos automáticamente
        if self.actividad_predefinida and self.estado_code not in ('aprobada', 'pendiente_inicio', 'en_curso'):
            estado_pendiente = self.env.ref('actividades_complementarias.estado_pendiente_inicio')
            self.write({'estado_id': estado_pendiente.id})
            self.message_post(body=f'Actividad predefinida ({self.actividad_predefinida}) aprobada automáticamente.')
        if self.estado_code not in ('aprobada', 'pendiente_inicio'):
            raise ValidationError('Solo se pueden enviar al catálogo actividades aprobadas o pendientes de inicio.')
        self.write({'en_catalogo': True})
        self.message_post(body='Actividad enviada al catálogo.')

    def action_iniciar_actividad(self):
        """Marca la actividad como En Curso manualmente."""
        self.ensure_one()
        if self.estado_code not in ('aprobada', 'pendiente_inicio'):
            raise ValidationError('Solo se pueden iniciar actividades aprobadas o pendientes de inicio.')
        estado_en_curso = self.env.ref('actividades_complementarias.estado_en_curso')
        self.write({'estado_id': estado_en_curso.id})
        self.message_post(body='Actividad iniciada manualmente por el Jefe de Departamento.')

    def action_finalizar_actividad(self):
        """Marca la actividad como Finalizada manualmente."""
        self.ensure_one()
        if self.estado_code != 'en_curso':
            raise ValidationError('Solo se pueden finalizar actividades que estén en curso.')
        estado_finalizada = self.env.ref('actividades_complementarias.estado_finalizada')
        self.write({'estado_id': estado_finalizada.id, 'en_catalogo': False})
        self.message_post(body='Actividad finalizada. Removida del catálogo automáticamente.')

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
            en_curso.write({'estado_id': estado_finalizada.id, 'en_catalogo': False})


class ActividadDepartamento(models.Model):
    """Catálogo simple de departamentos para asociar JD y personal."""
    _name = 'actividad.departamento'
    _description = 'Departamento'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    jefe_id = fields.Many2one('res.users', string='Jefe de Departamento')
