# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('actividades_complementarias', '-standard')
class TestPropuestaActividad(TransactionCase):
    """Tests para el modelo actividad.propuesta."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.estado_sol_en_revision = cls.env.ref(
            'actividades_complementarias.estado_solicitud_en_revision'
        )
        cls.estado_sol_aprobada = cls.env.ref(
            'actividades_complementarias.estado_solicitud_aprobada'
        )
        cls.estado_sol_rechazada = cls.env.ref(
            'actividades_complementarias.estado_solicitud_rechazada'
        )
        cls.estado_aprobada = cls.env.ref('actividades_complementarias.estado_aprobada')
        cls.estado_rechazada = cls.env.ref('actividades_complementarias.estado_rechazada')
        cls.periodo = cls.env.ref('actividades_complementarias.periodo_2025_A')

        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Taller Test'})

        hoy = date.today()
        cls.actividad = cls.env['actividad.complementaria'].create({
            'name': 'Actividad para Propuesta',
            'tipo_actividad_id': cls.tipo.id,
            'periodo': cls.periodo.id,
            'fecha_inicio': hoy + timedelta(days=1),
            'fecha_fin': hoy + timedelta(days=2),
            'cantidad_horas': 4.0,
        })

    def _make_propuesta(self, actividad=None, **kwargs):
        """Helper: crea una propuesta en estado 'en revisión'."""
        vals = {
            'actividad_id': (actividad or self.actividad).id,
            'estado_solicitud_id': self.estado_sol_en_revision.id,
        }
        vals.update(kwargs)
        return self.env['actividad.propuesta'].create(vals)

    # ── Computes ─────────────────────────────────────────────────────────────

    def test_encabezado_es_nombre_actividad(self):
        """El encabezado computado debe coincidir con el nombre de la actividad."""
        propuesta = self._make_propuesta()
        self.assertEqual(propuesta.encabezado, self.actividad.name)

    def test_fecha_limite_es_cinco_dias_despues(self):
        """La fecha límite de revisión debe ser 5 días después de la fecha de envío."""
        propuesta = self._make_propuesta()
        esperada = propuesta.fecha + timedelta(days=5)
        self.assertEqual(propuesta.fecha_limite_revision, esperada)

    def test_actividad_cupo_ilimitado(self):
        """El campo cupo debe mostrar 'Ilimitado' cuando cupo_ilimitado es True."""
        actividad_ilimitada = self.env['actividad.complementaria'].create({
            'name': 'Actividad Ilimitada Test',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': date.today() + timedelta(days=1),
            'fecha_fin': date.today() + timedelta(days=2),
            'cantidad_horas': 8.0,
            'cupo_ilimitado': True,
        })
        propuesta = self._make_propuesta(actividad=actividad_ilimitada)
        self.assertEqual(propuesta.actividad_cupo, 'Ilimitado')

    def test_actividad_cupo_rango(self):
        """El campo cupo debe mostrar el rango min–max cuando no es ilimitado."""
        propuesta = self._make_propuesta()
        self.assertIn('–', propuesta.actividad_cupo)

    # ── Business logic: aprobar ───────────────────────────────────────────────

    def test_action_aprobar_cambia_estados(self):
        """Aprobar una propuesta debe actualizar el estado de la propuesta y la actividad."""
        propuesta = self._make_propuesta()
        propuesta.action_aprobar()
        self.assertEqual(propuesta.estado_solicitud_id, self.estado_sol_aprobada)
        self.assertEqual(propuesta.actividad_id.estado_id, self.estado_aprobada)

    def test_action_aprobar_con_creditos_via_wizard(self):
        """El wizard de aprobación debe escribir los créditos en la actividad."""
        propuesta = self._make_propuesta()
        wizard = self.env['actividad.wizard.aprobar'].create({
            'propuesta_id': propuesta.id,
            'creditos': '1.5',
        })
        wizard.action_confirmar_aprobacion()
        self.assertEqual(propuesta.actividad_id.creditos, '1.5')
        self.assertEqual(propuesta.estado_code, 'aprobada')

    def test_wizard_aprobar_sin_creditos_falla(self):
        # Mute the SQL logger so the expected error doesn't print a traceback in the console
        with mute_logger('odoo.sql_db'), self.assertRaises(NotNullViolation):
            self.env['actividad.wizard.aprobar'].create({
                'nombre_actividad': 'Actividad para Propuesta',
                'propuesta_id': self.propuesta.id, # Ensure you use a valid ID here
                # 'creditos' is intentionally omitted to trigger the NotNullViolation
            })

    # ── Business logic: rechazar ──────────────────────────────────────────────

    def test_action_rechazar_sin_motivo_falla(self):
        """Rechazar sin motivo debe lanzar ValidationError."""
        propuesta = self._make_propuesta()
        with self.assertRaises(ValidationError):
            propuesta.action_rechazar()

    def test_action_rechazar_con_motivo_ok(self):
        """Rechazar con motivo debe actualizar los estados de propuesta y actividad."""
        propuesta = self._make_propuesta()
        propuesta.write({'motivo_rechazo': 'No cumple los requisitos mínimos.'})
        propuesta.action_rechazar()
        self.assertEqual(propuesta.estado_solicitud_id, self.estado_sol_rechazada)
        self.assertEqual(propuesta.actividad_id.estado_id, self.estado_rechazada)

    def test_wizard_rechazo_motivo_vacio_falla(self):
        """El wizard de rechazo debe fallar si el motivo está vacío."""
        propuesta = self._make_propuesta()
        wizard = self.env['actividad.wizard.rechazar'].create({
            'propuesta_id': propuesta.id,
            'motivo_rechazo': '   ',
        })
        with self.assertRaises(ValidationError):
            wizard.action_confirmar_rechazo()

    def test_wizard_rechazo_con_motivo_ok(self):
        """El wizard de rechazo debe funcionar correctamente con un motivo válido."""
        propuesta = self._make_propuesta()
        wizard = self.env['actividad.wizard.rechazar'].create({
            'propuesta_id': propuesta.id,
            'motivo_rechazo': 'Insuficiente justificación académica.',
        })
        wizard.action_confirmar_rechazo()
        self.assertEqual(propuesta.estado_code, 'rechazada')

    # ── Cron: auto-aprobación por vencimiento ────────────────────────────────

    def test_cron_auto_aprobar_propuestas_vencidas(self):
        """El cron debe aprobar propuestas cuya fecha límite ya pasó."""
        actividad_cron = self.env['actividad.complementaria'].create({
            'name': 'Actividad Cron Auto-Aprobación',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': date.today() + timedelta(days=1),
            'fecha_fin': date.today() + timedelta(days=2),
            'cantidad_horas': 4.0,
        })
        propuesta = self.env['actividad.propuesta'].create({
            'actividad_id': actividad_cron.id,
            'estado_solicitud_id': self.estado_sol_en_revision.id,
            'fecha': date.today() - timedelta(days=6),
        })
        # fecha_limite_revision es fecha + 5 días → ya venció
        self.env['actividad.propuesta']._auto_aprobar_propuestas_vencidas()
        self.assertEqual(propuesta.estado_code, 'aprobada')

    def test_cron_no_aprueba_propuestas_vigentes(self):
        """El cron NO debe aprobar propuestas cuya fecha límite aún no llegó."""
        actividad_cron = self.env['actividad.complementaria'].create({
            'name': 'Actividad Cron Vigente',
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.periodo.id,
            'fecha_inicio': date.today() + timedelta(days=1),
            'fecha_fin': date.today() + timedelta(days=2),
            'cantidad_horas': 4.0,
        })
        propuesta = self.env['actividad.propuesta'].create({
            'actividad_id': actividad_cron.id,
            'estado_solicitud_id': self.estado_sol_en_revision.id,
            'fecha': date.today() - timedelta(days=2),
        })
        self.env['actividad.propuesta']._auto_aprobar_propuestas_vencidas()
        self.assertEqual(propuesta.estado_code, 'en_revision')
