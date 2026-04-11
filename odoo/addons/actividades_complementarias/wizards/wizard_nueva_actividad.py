# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import models, fields, api
from odoo.exceptions import ValidationError


def _n_dias_habiles(n, desde=None):
    """Avanza *n* días hábiles (lunes a viernes) desde *desde* (default: hoy)."""
    base = desde if desde is not None else date.today()
    contados = 0
    candidato = base
    while contados < n:
        candidato += timedelta(days=1)
        if candidato.weekday() < 5:   # 0=lun … 4=vie
            contados += 1
    return candidato


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
    periodo = fields.Many2one('actividad.periodo', string='Periodo Escolar', required=True)
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
    actividad_predefinida = fields.Selection([
        ('curso_mooc', 'Curso MOOC'),
        ('extraescolar', 'Extraescolar'),
    ], string='Actividades Predefinidas',
       help='Seleccione si la actividad corresponde a un tipo predefinido. '
            'Estas no requieren aprobación del Comité Académico.'
    )
    responsable_actividad_id = fields.Many2one(
        'res.users', string='Responsable de Actividad'
    )
    creditos = fields.Selection([
        ('0.5', '0.5 créditos'),
        ('1.0', '1 crédito'),
        ('1.5', '1.5 créditos'),
        ('2.0', '2 créditos'),
    ], string='Cantidad de Créditos')

    # ────────────────────────────────────────────────────────────────────────
    @api.depends('tipo_actividad_id', 'actividad_predefinida')
    def _compute_es_predefinida(self):
        for rec in self:
            rec.es_predefinida = (
                bool(rec.actividad_predefinida) or
                (rec.tipo_actividad_id.es_predefinida if rec.tipo_actividad_id else False)
            )

    # ────────────────────────────────────────────────────────────────────────
    # Constraints
    # ────────────────────────────────────────────────────────────────────────

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if not self.env.context.get('install_demo') and not self.env.context.get('skip_fecha_check'):
                if rec.fecha_inicio:
                    min_fecha = _n_dias_habiles(5)
                    if rec.fecha_inicio < min_fecha:
                        raise ValidationError(
                            f'La fecha de inicio debe ser al menos 5 días hábiles '
                            f'a partir de hoy. La fecha mínima válida es '
                            f'{min_fecha.strftime("%d/%m/%Y")}.'
                        )
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
        Valida todos los campos, luego crea la actividad y la enruta:
        - Predefinida -> estado 'pendiente_inicio' (sin comite).
        - Nueva -> estado 'en_revision', se crea propuesta al Comite.
        """
        self.ensure_one()

        # --- Validaciones comunes (aplican siempre) -------------------------
        errores = []

        if not self.name or not self.name.strip():
            errores.append(u'\u2022 Nombre de la Actividad es obligatorio.')
        if not self.tipo_actividad_id:
            errores.append(u'\u2022 Tipo de Actividad es obligatorio.')
        if not self.periodo:
            errores.append(u'\u2022 Periodo Escolar es obligatorio.')
        if not self.fecha_inicio:
            errores.append(u'\u2022 Fecha de Inicio es obligatoria.')
        if not self.fecha_fin:
            errores.append(u'\u2022 Fecha de Finalizacion es obligatoria.')
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                errores.append(u'\u2022 La Fecha de Finalizacion debe ser posterior a la Fecha de Inicio.')
            if not self.env.context.get('install_demo') and self.fecha_inicio < date.today():
                errores.append(u'\u2022 La Fecha de Inicio no puede ser anterior a hoy.')
            dias = (self.fecha_fin - self.fecha_inicio).days + 1
            horas_max = dias * 12
            if self.cantidad_horas and self.cantidad_horas > horas_max:
                errores.append(
                    u'\u2022 La Cantidad de Horas (%g h) supera el maximo para el periodo '
                    u'seleccionado (%d dia(s) x 12 h = %d h maximos).' % (
                        self.cantidad_horas, dias, horas_max
                    )
                )
        if not self.cantidad_horas or self.cantidad_horas <= 0:
            errores.append(u'\u2022 La Cantidad de Horas debe ser mayor a 0.')
        if not self.cupo_ilimitado:
            if self.cupo_min < 1:
                errores.append(u'\u2022 El Cupo Minimo debe ser al menos 1.')
            if self.cupo_max < self.cupo_min:
                errores.append(u'\u2022 El Cupo Maximo debe ser mayor o igual al Cupo Minimo.')

        # --- Validaciones extra para actividades predefinidas ---------------
        es_predefinida_check = (
            bool(self.actividad_predefinida) or
            (self.tipo_actividad_id.es_predefinida if self.tipo_actividad_id else False)
        )
        if es_predefinida_check:
            if not self.creditos:
                errores.append(u'\u2022 Cantidad de Creditos es obligatoria para enviar al Catalogo.')
            if not self.responsable_actividad_id:
                errores.append(u'\u2022 Responsable de Actividad es obligatorio para enviar al Catalogo.')
        else:
            # Para enviar al Comite la cantidad de horas tambien debe ser > 0 (ya cubierto arriba)
            if not self.creditos:
                errores.append(u'\u2022 Cantidad de Creditos es obligatoria para enviar al Comite Academico.')

        if errores:
            raise ValidationError(
                u'Por favor corrija los siguientes campos antes de continuar:\n\n' +
                u'\n'.join(errores)
            )

        # Determinar si es predefinida
        es_predefinida = (
            bool(self.actividad_predefinida) or
            (self.tipo_actividad_id.es_predefinida if self.tipo_actividad_id else False)
        )

        if es_predefinida:
            estado = self.env.ref('actividades_complementarias.estado_pendiente_inicio')
        else:
            estado = self.env.ref('actividades_complementarias.estado_en_revision')

        vals = {
            'name': self.name,
            'descripcion': self.descripcion,
            'tipo_actividad_id': self.tipo_actividad_id.id,
            'periodo': self.periodo.id,
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
            'responsable_actividad_id': (
                self.responsable_actividad_id.id if self.responsable_actividad_id else False
            ),
            'creditos': self.creditos,
        }

        if es_predefinida:
            vals['en_catalogo'] = False

        actividad = self.env['actividad.complementaria'].with_context(
            skip_fecha_check=True, skip_horas_check=True
        ).create(vals)

        if not es_predefinida:
            # Crear propuesta al comité en estado "en revisión"
            estado_revision = self.env.ref('actividades_complementarias.estado_solicitud_en_revision')
            self.env['actividad.propuesta'].create({
                'actividad_id': actividad.id,
                'estado_solicitud_id': estado_revision.id,
            })
            actividad.message_post(
                body='Propuesta enviada al Comité Académico para su revisión. '
                     'Se aprobará automáticamente si no hay respuesta en 5 días.'
            )
        else:
            tipo_label = dict(self._fields['actividad_predefinida'].selection).get(
                self.actividad_predefinida, self.tipo_actividad_id.name
            ) if self.actividad_predefinida else self.tipo_actividad_id.name
            actividad.message_post(
                body=f'Actividad predefinida ({tipo_label}) registrada y aprobada automáticamente. '
                     f'Lista para enviar al catálogo.'
            )

        # Redirigir según el tipo de actividad
        if not es_predefinida:
            # Enviada al comité → ir a "Mis Propuestas al Comité"
            action = self.env.ref(
                'actividades_complementarias.action_propuesta',
                raise_if_not_found=False,
            )
            if action:
                result = action.sudo().read()[0]
                result['target'] = 'current'
                return result
        # Predefinida → abrir el registro para que el JD pueda enviarlo al catálogo
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'actividad.complementaria',
            'res_id': actividad.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancelar(self):
        return {'type': 'ir.actions.act_window_close'}
