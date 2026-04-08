# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


def _n_dias_habiles(n, desde=None):
    """Avanza *n* días hábiles (lunes a viernes) desde *desde*.

    Args:
        n:     Número de días hábiles a avanzar.
        desde: Fecha base. Si es None se usa la fecha actual.
    Returns:
        date con la fecha resultante.
    """
    base = desde if desde is not None else date.today()
    contados = 0
    candidato = base
    while contados < n:
        candidato += timedelta(days=1)
        if candidato.weekday() < 5:   # 0=lun … 4=vie; 5=sáb, 6=dom
            contados += 1
    return candidato


class Actividad(models.Model):
    _name = 'actividad.complementaria'
    _description = 'Actividad Complementaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc'

    # Campos que el JD nunca puede escribir directamente (gestionados por el sistema).
    # Las acciones de negocio que los necesiten deben usar:
    #   self.with_context(bypass_edit_protection=True).write(vals)
    _CAMPOS_AUTO_JD = frozenset({
        'jefe_departamento_id',
        'departamento_id',
        'estado_id',
        'en_catalogo',
        'jd_firmo',
        'responsable_firmo',
    })

    # XML-IDs de los grupos de Personal de Departamento.
    _GRUPOS_PERSONAL = (
        'actividades_complementarias.group_personal_departamento_sistemas',
        'actividades_complementarias.group_personal_departamento_electrica',
        'actividades_complementarias.group_personal_departamento_biologia',
        'actividades_complementarias.group_personal_departamento_extraescolar',
    )

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
    responsable_bloqueado = fields.Boolean(
        string='Responsable Bloqueado',
        default=False,
        help='Una vez confirmado, el Responsable de Actividad no puede cambiarse.',
        tracking=True,
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
    horas_maximas = fields.Float(
        string='Máximo de Horas',
        compute='_compute_horas_maximas',
        store=False,
        help='Máximo de horas permitidas según el rango de fechas (12 h por día).',
    )
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
    # Dual-signature: both JD and Responsable must sign before constancias reach students
    jd_firmo = fields.Boolean(string='Firmado por Jefe de Departamento', default=False, tracking=True)
    responsable_firmo = fields.Boolean(string='Firmado por Responsable de Actividad', default=False, tracking=True)
    constancias_firmadas = fields.Boolean(
        string='Constancias Firmadas',
        compute='_compute_constancias_firmadas',
        store=True,
        help='True solo cuando tanto el JD como el Responsable de Actividad han firmado.',
    )
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
    # ── Flags de permisos de edición (por estado) ─
    permisos_actividad_pendiente_inicio = fields.Boolean(
        string='Solo Responsable, Fechas y Horas Editables',
        compute='_compute_permisos_edicion',
        help='True cuando el JD solo puede modificar los campos Responsable de Actividad, Fecha de Inicio, '
        'Fecha de Finalización y Horario por Día.',
    )
    permisos_actividad_en_curso = fields.Boolean(
        string='Solo Responsable Editable',
        compute='_compute_permisos_edicion',
        help='True cuando el JD solo puede modificar el campo Responsable de Actividad.',
    )
    permisos_actividad_finalizada = fields.Boolean(
        string='Solo Lectura',
        compute='_compute_permisos_edicion',
        help='True cuando el usuario en sesión no puede editar ningún campo del formulario.',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Helpers de rol
    # ────────────────────────────────────────────────────────────────────────

    def _es_personal(self):
        """True si el usuario en sesion pertenece a algun grupo de Personal."""
        return any(self.env.user.has_group(g) for g in self._GRUPOS_PERSONAL)

    def _get_permiso_personal(self):
        """Devuelve el registro EmpleadoPermiso del usuario en sesion o vacio."""
        return self.env['actividad.empleado.permiso'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1
        )

    # ────────────────────────────────────────────────────────────────────────
    # ORM override: _search() -- filtrado automatico para Personal
    # ────────────────────────────────────────────────────────────────────────

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        """Restringe la busqueda del Personal al departamento propio + catalogo."""
        is_admin = self.env.user.has_group(
            'actividades_complementarias.group_admin_actividades'
        )
        is_jd = self.env.user.has_group(
            'actividades_complementarias.group_jefe_departamento'
        )
        if not is_admin and not is_jd and self._es_personal():
            permiso = self._get_permiso_personal()
            if permiso and permiso.departamento_id:
                dept_id = permiso.departamento_id.id
                dept_domain = [
                    '|',
                    ('departamento_id', '=', dept_id),
                    ('en_catalogo', '=', True),
                ]
            else:
                dept_domain = [('en_catalogo', '=', True)]
            domain = dept_domain + list(domain)
        return super()._search(
            domain, offset=offset, limit=limit, order=order, **kwargs
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

    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_horas_maximas(self):
        """12 horas por día del rango (fecha_fin - fecha_inicio + 1)."""
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin and rec.fecha_fin >= rec.fecha_inicio:
                dias = (rec.fecha_fin - rec.fecha_inicio).days + 1
                rec.horas_maximas = dias * 12.0
            else:
                rec.horas_maximas = 0.0

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _onchange_fechas_ajustar_horas(self):
        """Si las horas ya cargadas superan el nuevo máximo, las recorta al máximo."""
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin >= self.fecha_inicio:
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            maximo = dias * 12.0
            if self.cantidad_horas and self.cantidad_horas > maximo:
                self.cantidad_horas = maximo

    @api.onchange('tipo_actividad_id')
    def _onchange_tipo_actividad_limpiar_predefinida(self):
        """Borra actividad_predefinida cuando el tipo es 'Nueva (Propuesta)'.
        Evita que una actividad tipo nueva pueda saltarse el Comite Academico."""
        if self.tipo_actividad_id and self.tipo_actividad_id.name == 'Nueva (Propuesta)':
            self.actividad_predefinida = False
            self.responsable_actividad_id = False

    @api.onchange('actividad_predefinida')
    def _onchange_actividad_predefinida_limpiar_responsable(self):
        """Borra el responsable cuando se quita la selección de actividad predefinida.
        El campo responsable solo aplica a actividades predefinidas en creación."""
        if not self.actividad_predefinida and not self.estado_code:
            self.responsable_actividad_id = False

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
                emp = self.env['actividad.empleado.permiso'].search(
                    [('user_id', '=', rec.jefe_departamento_id.id)], limit=1
                )
                rec.departamento_id = emp.departamento_id if emp else False

    @api.depends('jd_firmo', 'responsable_firmo')
    def _compute_constancias_firmadas(self):
        for rec in self:
            rec.constancias_firmadas = rec.jd_firmo and rec.responsable_firmo

    @api.depends('alumno_ids')
    def _compute_alumno_count(self):
        for rec in self:
            rec.alumno_count = len(rec.alumno_ids)

    @api.depends('estado_code', 'en_catalogo', 'jefe_departamento_id')
    def _compute_permisos_edicion(self):
        """
        Calcula los flags de solo-lectura para el formulario según el estado
        del registro y el rol del usuario en sesión.

        Las reglas implementadas son:
        1. Finalizada             → permisos_actividad_finalizada=True para TODOS (incluido admin).
        2. Admin (no finalizada)  → sin restricciones de formulario.
        3. JD dueño, en_revision  → permisos_actividad_finalizada=True.
        4. JD dueño, pendiente de inicio → permisos_actividad_pendiente_inicio = True
        5. JD dueño, en_catalogo
           o pendiente_inicio
           o en_curso             → permisos_actividad_en_curso=True.
        6. JD dueño, rechazada
           o aprobada             → sin restricciones (puede editar campos no-auto).
        7. JD viendo actividad
           de otro JD             → permisos_actividad_finalizada=True (solo puede ver catálogo).
        8. Cualquier otro rol     → permisos_actividad_finalizada=True.
        """
        is_admin = self.env.user.has_group(
            'actividades_complementarias.group_admin_actividades'
        )
        is_jd = self.env.user.has_group(
            'actividades_complementarias.group_jefe_departamento'
        )

        for rec in self:
            # Regla 1 (absoluta): finalizada → nadie edita
            if rec.estado_code == 'finalizada':
                rec.permisos_actividad_finalizada = True
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False
                continue

            # Admin: sin restricciones de solo-lectura (salvo finalizada)
            if is_admin:
                rec.permisos_actividad_finalizada = False
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False
                continue

            if not is_jd:
                # Otros roles: formulario de solo lectura
                rec.permisos_actividad_finalizada = True
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False
                continue

            # Usuario es JD (no admin)
            es_dueno = (rec.jefe_departamento_id.id == self.env.user.id)

            if not es_dueno:
                # Regla 6: JD viendo actividad de otro JD (solo catálogo accesible via record rule)
                rec.permisos_actividad_finalizada = True
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False

            elif rec.estado_code in ('aprobada', 'pendiente_inicio'):
                # Regla 4: actividad pendiende de inicio
                rec.permisos_actividad_finalizada = False
                rec.permisos_actividad_pendiente_inicio = True
                rec.permisos_actividad_en_curso = False

            elif rec.estado_code == 'en_revision':
                # Regla 2/3: propuesta en revisión → JD no puede modificar nada
                rec.permisos_actividad_finalizada = True
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False

            elif rec.en_catalogo or rec.estado_code == 'en_curso':
                # Regla 3: en catálogo o iniciada → solo responsable_actividad_id
                rec.permisos_actividad_finalizada = False
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = True

            else:
                # Regla 4: rechazada, aprobada u otro estado → acceso completo (no-auto)
                rec.permisos_actividad_finalizada = False
                rec.permisos_actividad_pendiente_inicio = False
                rec.permisos_actividad_en_curso = False

    # ────────────────────────────────────────────────────────────────────────
    # ORM override: create()
    # ────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        """Estampa el flag actividad_creating=True en el contexto para que
        _check_fechas pueda distinguir una creación de una edición.

        El flag se elimina del recordset devuelto para que llamadas
        posteriores a write() sobre esos registros no lo hereden.
        """
        records = super(
            Actividad,
            self.with_context(actividad_creating=True),
        ).create(vals_list)
        return records.with_context(actividad_creating=False)

    # ────────────────────────────────────────────────────────────────────────
    # ORM override: write()
    # ────────────────────────────────────────────────────────────────────────

    def write(self, vals):
        """
        Aplica las reglas de edición según estado y rol del usuario en sesión.

        Para que las acciones de negocio internas (cron, wizards, flujo de trabajo)
        puedan modificar campos auto-gestionados o registros finalizados, deben usar:
            self.with_context(bypass_edit_protection=True).write(vals)
        """
        # Las acciones internas del sistema omiten la protección
        if self.env.context.get('bypass_edit_protection'):
            return super().write(vals)

        is_admin = self.env.user.has_group(
            'actividades_complementarias.group_admin_actividades'
        )
        is_jd = self.env.user.has_group(
            'actividades_complementarias.group_jefe_departamento'
        )

        for rec in self:
            # ── Regla 1: Finalizada → nadie puede modificar (incluido admin) ──
            if rec.estado_code == 'finalizada':
                raise UserError(
                    _('La actividad "%s" está finalizada y no puede ser '
                      'modificada por ningún usuario.')
                    % rec.name
                )

            # Admin: sin restricciones de estado
            if is_admin:
                continue

            # ── Personal de Departamento ──────────────────────────────────────
            if not is_jd and self._es_personal():
                permiso = self._get_permiso_personal()
                if not permiso:
                    raise UserError(
                        _('No tiene permisos delegados para modificar '
                          'actividades complementarias.')
                    )
                # Solo puede modificar actividades de su propio departamento
                if rec.departamento_id != permiso.departamento_id:
                    raise UserError(
                        _('No tiene permiso para modificar actividades '
                          'de otros departamentos.')
                    )
                # Verificar permiso granular segun los campos modificados
                campos_vals = set(vals.keys())
                if 'alumno_ids' in campos_vals and not permiso.perm_asignar_alumnos:
                    raise UserError(
                        _('No tiene el permiso "Asignar Alumnos a Actividad".')
                    )
                if 'en_catalogo' in campos_vals and not permiso.perm_enviar_catalogo:
                    raise UserError(
                        _('No tiene el permiso "Enviar al Catalogo".')
                    )
                campos_generales = campos_vals - {'alumno_ids', 'en_catalogo'}
                if campos_generales and not permiso.perm_modificar_actividades:
                    raise UserError(
                        _('No tiene el permiso "Modificar Actividades '
                          'Complementarias".')
                    )
                continue

            # Otros roles sin gestion especial
            if not is_jd:
                continue

            # ── A partir de aqui: usuario es JD (no admin) ──

            # ── Regla 5: JD nunca modifica actividades de otro JD ──
            if rec.jefe_departamento_id.id != self.env.user.id:
                raise UserError(
                    _('No tiene permiso para modificar actividades de '
                      'otros Jefes de Departamento.')
                )

            # JD no puede escribir directamente campos auto-gestionados
            campos_auto_solicitados = set(vals.keys()) & self._CAMPOS_AUTO_JD
            if campos_auto_solicitados:
                raise UserError(
                    _('Los siguientes campos son gestionados automáticamente '
                      'por el sistema y no pueden modificarse directamente: %s.')
                    % ', '.join(sorted(campos_auto_solicitados))
                )

            # ── Regla 2: Propuesta en revisión → JD no modifica nada ──
            if rec.estado_code == 'en_revision':
                raise UserError(
                    _('La propuesta de la actividad "%s" está siendo revisada '
                      'por el Comité Académico. No puede modificarla durante la revisión.')
                    % rec.name
                )
            # ── Regla 3: En catálogo / Pendiente de Inicio ──
            if rec.en_catalogo or rec.estado_code in ('aprobada', 'pendiente_inicio'):
                campos_permitidos = {'responsable_actividad_id', 'fecha_inicio', 'fecha_fin', 'horario'}
                campos_no_permitidos = set(vals.keys()) - campos_permitidos
                if campos_no_permitidos:
                    raise UserError(
                        _('La actividad "%s" está en aprobada o pendiente de inicio. '
                          'En este estado únicamente puede modificar'
                          '"Responsable de Actividad", "Fecha de Inicio", "Fecha de Finalización", '
                          'y "Horario por Día".')
                        % rec.name
                    )

            # ── Regla 3: En catálogo / En Curso ──
            #    Solo se permite modificar responsable_actividad_id
            if rec.estado_code == 'en_curso':
                campos_permitidos = {'responsable_actividad_id'}
                campos_no_permitidos = set(vals.keys()) - campos_permitidos
                if campos_no_permitidos:
                    raise UserError(
                        _('La actividad "%s" está en curso. '
                          'En este estado únicamente puede modificar '
                          '"Responsable de Actividad".')
                        % rec.name
                    )

            # ── Regla 4: Rechazada → JD puede modificar cualquier campo
            #    que no sea auto-gestionado (ya validado arriba). ──

        return super().write(vals)

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        bypass = (
            self.env.context.get('install_demo')
            or self.env.context.get('skip_fecha_check')
        )
        manana = date.today() + timedelta(days=1)
        for rec in self:
            if rec.fecha_inicio and not bypass:
                # True durante create() gracias al flag que estampa el override;
                # False durante write() donde el flag no está presente.
                es_nuevo = self.env.context.get('actividad_creating', False)
                if es_nuevo:
                    # Al crear: mínimo 5 días hábiles desde hoy
                    min_fecha = _n_dias_habiles(5)
                    if rec.fecha_inicio < min_fecha:
                        raise ValidationError(
                            _(
                                'La fecha de inicio debe ser al menos 5 días hábiles '
                                '(sin domingos) a partir de hoy. '
                                'La fecha mínima válida es %(fecha)s.',
                                fecha=min_fecha.strftime('%d/%m/%Y'),
                            )
                        )
                else:
                    # En edición: si existe propuesta aprobada, el mínimo se calcula
                    # como 5 días hábiles contados desde la fecha de envío de esa propuesta,
                    # de modo que el tiempo total (envío → inicio) sea al menos 5 días hábiles.
                    # Piso absoluto: siempre al menos mañana.
                    propuesta = self.env['actividad.propuesta'].search(
                        [
                            ('actividad_id', '=', rec.id),
                            ('estado_code', '=', 'aprobada'),
                        ],
                        order='fecha desc',
                        limit=1,
                    )
                    if propuesta:
                        min_desde_propuesta = _n_dias_habiles(5, desde=propuesta.fecha)
                        min_fecha = max(min_desde_propuesta, manana)
                    else:
                        min_fecha = manana

                    if rec.fecha_inicio < min_fecha:
                        raise ValidationError(
                            _(
                                'La fecha de inicio no puede ser anterior a %(fecha)s.',
                                fecha=min_fecha.strftime('%d/%m/%Y'),
                            )
                        )
            if rec.fecha_fin and rec.fecha_inicio and rec.fecha_fin <= rec.fecha_inicio:
                raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')

    @api.constrains('name', 'periodo')
    def _check_nombre_unico_periodo(self):
        for rec in self:
            domain = [
                ('name', '=ilike', rec.name),
                ('periodo', '=', rec.periodo.id),
                ('id', '!=', rec.id),
                ('estado_code', 'not in', ['rechazada', 'finalizada']),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    f'Ya existe una actividad activa con el nombre "{rec.name}" en el periodo {rec.periodo.name}.'
                )

    @api.constrains('cupo_min', 'cupo_max', 'cupo_ilimitado')
    def _check_cupos(self):
        for rec in self:
            if not rec.cupo_ilimitado:
                if rec.cupo_min < 1:
                    raise ValidationError('El cupo mínimo debe ser al menos 1.')
                if rec.cupo_max < rec.cupo_min:
                    raise ValidationError('El cupo máximo debe ser mayor o igual al cupo mínimo.')

    @api.constrains('cantidad_horas', 'fecha_inicio', 'fecha_fin')
    def _check_horas_vs_dias(self):
        """La cantidad de horas no puede exceder el total de horas disponibles
        en el rango de fechas (dias * 12 h como tope). Se omite en carga de demo."""
        if self.env.context.get('install_demo') or self.env.context.get('skip_horas_check'):
            return
        for rec in self:
            if rec.fecha_inicio and rec.fecha_fin and rec.cantidad_horas:
                dias = (rec.fecha_fin - rec.fecha_inicio).days + 1
                horas_maximas = dias * 12
                if rec.cantidad_horas > horas_maximas:
                    raise ValidationError(
                        f'La cantidad de horas ({rec.cantidad_horas} h) no puede ser mayor '
                        f'al máximo permitido para el período seleccionado '
                        f'({dias} día(s) × 12 h = {horas_maximas} h máximo).'
                    )
                if rec.cantidad_horas <= 0:
                    raise ValidationError('La cantidad de horas debe ser mayor a 0.')

    @api.constrains('alumno_ids', 'cupo_max', 'cupo_ilimitado')
    def _check_cupo_alumnos(self):
        """Valida que el número de alumnos no supere el cupo máximo permitido."""
        for rec in self:
            if not rec.cupo_ilimitado and len(rec.alumno_ids) > rec.cupo_max:
                raise ValidationError(
                    f'No se pueden añadir más alumnos. '
                    f'La actividad "{rec.name}" tiene un cupo máximo de '
                    f'{rec.cupo_max} alumno(s) y actualmente hay '
                    f'{len(rec.alumno_ids)} inscrito(s).'
                )

    # ────────────────────────────────────────────────────────────────────────
    # Business Logic
    # Todas las acciones de negocio que escriben campos auto-gestionados
    # usan with_context(bypass_edit_protection=True) para pasar el guard de write().
    # ────────────────────────────────────────────────────────────────────────

    def action_abrir_wizard_responsable(self):
        """Abre el wizard de confirmación para asignar el Responsable de Actividad."""
        self.ensure_one()
        if self.responsable_bloqueado:
            raise ValidationError(
                'El Responsable de Actividad ya fue asignado y no puede modificarse.'
            )
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asignar Responsable de Actividad',
            'res_model': 'actividad.wizard.asignar.responsable',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_actividad_id': self.id},
        }

    def action_enviar_comite(self):
        """Envia la actividad como propuesta al Comite Academico.
        Permite reenvio cuando la propuesta fue rechazada previamente."""
        self.ensure_one()
        if self._es_personal():
            permiso = self._get_permiso_personal()
            if not permiso or not permiso.perm_modificar_actividades:
                raise UserError(
                    _('No tiene el permiso "Modificar Actividades Complementarias" '
                      'para enviar una propuesta al Comite Academico.')
                )
        if self.estado_code in ('aprobada', 'pendiente_inicio', 'en_curso', 'finalizada'):
            raise ValidationError(
                'Esta actividad ya fue aprobada o está en curso/finalizada. '
                'No puede ser reenviada al Comité Académico.'
            )
        # Validar cantidad de horas > 0
        if not self.cantidad_horas or self.cantidad_horas <= 0:
            raise ValidationError(
                'La cantidad de horas debe ser mayor a 0 antes de enviar al Comité Académico.'
            )
        # Validar que tenga creditos asignados
        if not self.creditos:
            raise ValidationError(
                'Debe asignar la cantidad de créditos antes de enviar al Comité Académico.'
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
        self.with_context(bypass_edit_protection=True).write({'estado_id': estado_en_revision.id})
        self.env['actividad.propuesta'].create({
            'actividad_id': self.id,
            'estado_solicitud_id': estado_revision_solicitud.id,
        })
        self.message_post(
            body='Propuesta enviada al Comité Académico para su revisión. '
                 'Se aprobará automáticamente si no hay respuesta en 5 días.'
        )
        # Redirigir a "Mis Propuestas al Comité" (lista completa, sin filtro por actividad)
        action = self.env.ref(
            'actividades_complementarias.action_propuesta',
            raise_if_not_found=False,
        )
        if action:
            result = action.read()[0]
            result['target'] = 'current'
            return result
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mis Propuestas al Comité',
            'res_model': 'actividad.propuesta',
            'view_mode': 'list,form',
            'domain': [('actividad_id.jefe_departamento_id', '=', self.env.user.id)],
            'target': 'current',
        }

    def action_enviar_catalogo(self):
        """Envia la actividad al catalogo."""
        self.ensure_one()
        if self._es_personal():
            permiso = self._get_permiso_personal()
            if not permiso or not permiso.perm_enviar_catalogo:
                raise UserError(
                    _('No tiene el permiso "Enviar al Catalogo".')
                )
        if self.estado_code == 'rechazada':
            raise ValidationError(
                'Las actividades rechazadas no pueden ser enviadas al catálogo.'
            )
        if self.estado_code == 'finalizada':
            raise ValidationError(
                'Esta actividad ya fue finalizada y no puede ser enviada al catálogo. '
                'Cree una nueva propuesta de actividad si desea volver a ofertarla.'
            )
        # Validar horas > 0
        if not self.cantidad_horas or self.cantidad_horas <= 0:
            raise ValidationError(
                'La cantidad de horas debe ser mayor a 0 antes de enviar al catálogo.'
            )
        # Validar créditos obligatorios
        if not self.creditos:
            raise ValidationError(
                'Debe asignar la cantidad de créditos antes de enviar al catálogo.'
            )
        # Validar responsable obligatorio
        if not self.responsable_actividad_id:
            raise ValidationError(
                'Debe asignar un Responsable de Actividad antes de enviar al catálogo.'
            )
        # Si es predefinida y aún no está en un estado válido, la aprobamos automáticamente
        if self.actividad_predefinida and self.estado_code not in ('aprobada', 'pendiente_inicio', 'en_curso'):
            estado_pendiente = self.env.ref('actividades_complementarias.estado_pendiente_inicio')
            self.write({'estado_id': estado_pendiente.id})
            self.message_post(
                body='Actividad predefinida (%s) aprobada automáticamente.' % self.actividad_predefinida
            )
        if self.estado_code not in ('aprobada', 'pendiente_inicio'):
            raise ValidationError('Solo se pueden enviar al catálogo actividades aprobadas o pendientes de inicio.')
        self.with_context(bypass_edit_protection=True).write({'en_catalogo': True})
        self.message_post(body='Actividad enviada al catálogo.')
        # Redirigir al catálogo de actividades (no quedar en vista superpuesta)
        action = self.env.ref(
            'actividades_complementarias.action_actividad_catalogo',
            raise_if_not_found=False,
        )
        if action:
            result = action.read()[0]
            result['target'] = 'current'
            return result
        return {'type': 'ir.actions.act_window_close'}

    def action_iniciar_actividad(self):
        """Marca la actividad como En Curso manualmente."""
        self.ensure_one()
        if self.estado_code not in ('aprobada', 'pendiente_inicio'):
            raise ValidationError('Solo se pueden iniciar actividades aprobadas o pendientes de inicio.')
        estado_en_curso = self.env.ref('actividades_complementarias.estado_en_curso')
        self.with_context(bypass_edit_protection=True).write({'estado_id': estado_en_curso.id})
        self.message_post(body='Actividad iniciada manualmente por el Jefe de Departamento.')

    def action_finalizar_actividad(self):
        """Marca la actividad como Finalizada manualmente."""
        self.ensure_one()
        if self.estado_code != 'en_curso':
            raise ValidationError('Solo se pueden finalizar actividades que estén en curso.')
        estado_finalizada = self.env.ref('actividades_complementarias.estado_finalizada')
        self.with_context(bypass_edit_protection=True).write({
            'estado_id': estado_finalizada.id,
            'en_catalogo': False,
        })
        self.message_post(body='Actividad finalizada. Removida del catálogo automáticamente.')

    def action_firmar_constancias(self):
        """El JD firma su parte. Las constancias solo se liberan cuando ambos firmen."""
        self.ensure_one()
        if self.estado_code != 'finalizada':
            raise ValidationError('Solo se pueden firmar constancias de actividades finalizadas.')
        if self.jd_firmo:
            raise ValidationError('El Jefe de Departamento ya firmó las constancias de esta actividad.')
        # La firma es una acción de negocio válida sobre una actividad finalizada
        self.with_context(bypass_edit_protection=True).write({'jd_firmo': True})
        if self.constancias_firmadas:
            self.message_post(
                body='Constancias firmadas por el Jefe de Departamento. '
                     'Ambas firmas completas — constancias liberadas a expedientes.'
            )
        else:
            self.message_post(
                body='Constancias firmadas por el Jefe de Departamento. '
                     'Pendiente firma del Responsable de Actividad.'
            )

    def action_firmar_constancias_responsable(self):
        """El Responsable de Actividad firma su parte. Las constancias solo se liberan cuando ambos firmen."""
        self.ensure_one()
        if self.estado_code != 'finalizada':
            raise ValidationError('Solo se pueden firmar constancias de actividades finalizadas.')
        if self.responsable_firmo:
            raise ValidationError('El Responsable de Actividad ya firmó las constancias de esta actividad.')
        # La firma es una acción de negocio válida sobre una actividad finalizada
        self.with_context(bypass_edit_protection=True).write({'responsable_firmo': True})
        if self.constancias_firmadas:
            self.message_post(
                body='Constancias firmadas por el Responsable de Actividad. '
                     'Ambas firmas completas — constancias liberadas a expedientes.'
            )
        else:
            self.message_post(
                body='Constancias firmadas por el Responsable de Actividad. '
                     'Pendiente firma del Jefe de Departamento.'
            )

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
            pendientes.with_context(bypass_edit_protection=True).write(
                {'estado_id': estado_en_curso.id}
            )

        if estado_finalizada:
            en_curso = self.search([
                ('estado_code', '=', 'en_curso'),
                ('fecha_fin', '<=', hoy),
            ])
            en_curso.with_context(bypass_edit_protection=True).write({
                'estado_id': estado_finalizada.id,
                'en_catalogo': False,
            })


class ActividadDepartamento(models.Model):
    """Catálogo simple de departamentos para asociar JD y personal."""
    _name = 'actividad.departamento'
    _description = 'Departamento'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    jefe_id = fields.Many2one('res.users', string='Jefe de Departamento')
