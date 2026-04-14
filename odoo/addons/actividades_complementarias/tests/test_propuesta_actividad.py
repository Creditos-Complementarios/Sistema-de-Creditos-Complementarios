# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('actividades_complementarias', '-standard')
class TestPropuestaActividad(TransactionCase):
    """Tests para el modelo actividad.propuesta.

    Todos los estados y periodos se obtienen con env.ref() usando los xmlids
    definidos en los archivos de datos del módulo.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Estados de solicitud — definidos en estado_solicitud_data.xml
        cls.estado_sol_en_revision = cls.env.ref(
            'actividades_complementarias.estado_solicitud_en_revision'
        )
        cls.estado_sol_aprobada = cls.env.ref(
            'actividades_complementarias.estado_solicitud_aprobada'
        )
        cls.estado_sol_rechazada = cls.env.ref(
            'actividades_complementarias.estado_solicitud_rechazada'
        )

        # Estados de actividad — definidos en estado_actividad_data.xml
        cls.estado_aprobada = cls.env.ref('actividades_complementarias.estado_aprobada')
        cls.estado_rechazada = cls.env.ref('actividades_complementarias.estado_rechazada')

        # Periodo — Many2one, definido en periodo_data.xml
        cls.periodo = cls.env.ref('actividades_complementarias.per_2025A')

        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Taller Test'})

        hoy = date.today()
        cls.actividad = cls.env['actividad.complementaria'].with_context(
            skip_fecha_check=True
        ).create({
            'name': 'Actividad para Propuesta',
            'tipo_actividad_id': cls.tipo.id,
            'periodo': cls.periodo.id,   # Many2one: pasar el ID del registro
            'fecha_inicio': hoy + timedelta(days=1),
            'fecha_fin': hoy + timedelta(days=2),
            'cantidad_horas': 4.0,
            'creditos': '1.0',
        })

    def _make_propuesta(self, **kwargs):
        """Helper: crea una propuesta en estado 'en revisión'."""
        vals = {
            'actividad_id': self.actividad.id,
            'estado_solicitud_id': self.estado_sol_en_revision.id,
        }
        vals.update(kwargs)
        return self.env['actividad.propuesta'].create(vals)

    # ── Computes ─────────────────────────────────────────────────────────────

    def test_encabezado_es_nombre_actividad(self):
        """El encabezado computado debe coincidir con el nombre de la actividad."""
        propuesta = self._make_propuesta()
        self.assertEqual(propuesta.encabezado, self.actividad.name)

    def test_fecha_envio_es_hoy(self):
        """La fecha de envío de la propuesta debe ser la fecha actual en la zona horaria del usuario."""
        propuesta = self._make_propuesta()
        self.assertEqual(propuesta.fecha, fields.Date.context_today(propuesta))
        """La fecha límite de revisión debe ser 5 días después de la fecha de envío."""
        propuesta = self._make_propuesta()
        esperada = propuesta.fecha + timedelta(days=5)
        self.assertEqual(propuesta.fecha_limite_revision, esperada)

    # ── Business logic ───────────────────────────────────────────────────────

    def test_action_aprobar_cambia_estados(self):
        """Aprobar una propuesta debe actualizar el estado de la propuesta y la actividad."""
        propuesta = self._make_propuesta()
        propuesta.action_aprobar()
        self.assertEqual(propuesta.estado_solicitud_id, self.estado_sol_aprobada)
        self.assertEqual(propuesta.actividad_id.estado_id, self.estado_aprobada)

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

    # ── Predefinidas por Comité ───────────────────────────────────────────────

    def test_aprobar_crea_predefinida_comite(self):
        """Al aprobar una propuesta se debe crear un registro en
        actividad.tipo.predefinida con is_comite=True."""
        propuesta = self._make_propuesta()
        propuesta.action_aprobar()

        predefinida = self.env['actividad.tipo.predefinida'].search([
            ('name', '=', self.actividad.name),
            ('is_comite', '=', True),
        ])
        self.assertEqual(len(predefinida), 1)
        self.assertEqual(
            predefinida.tipo_actividad_id,
            self.actividad.tipo_actividad_id,
        )
        self.assertEqual(predefinida.actividad_origen_id, self.actividad)

    def test_aprobar_no_duplica_predefinida(self):
        """Aprobar dos propuestas con el mismo nombre de actividad no debe
        crear registros duplicados en actividad.tipo.predefinida."""
        import datetime
        hoy = datetime.date.today()

        actividad2 = self.env['actividad.complementaria'].with_context(
            skip_fecha_check=True
        ).create({
            'name': self.actividad.name,   # mismo nombre
            'tipo_actividad_id': self.tipo.id,
            'periodo': self.env.ref(
                'actividades_complementarias.per_2025B'
            ).id,
            'fecha_inicio': hoy + datetime.timedelta(days=1),
            'fecha_fin': hoy + datetime.timedelta(days=2),
            'cantidad_horas': 4.0,
            'creditos': '1.0',
        })

        propuesta1 = self._make_propuesta()
        propuesta1.action_aprobar()

        propuesta2 = self.env['actividad.propuesta'].create({
            'actividad_id': actividad2.id,
            'estado_solicitud_id': self.estado_sol_en_revision.id,
        })
        propuesta2.action_aprobar()

        count = self.env['actividad.tipo.predefinida'].search_count([
            ('name', '=', self.actividad.name),
            ('is_comite', '=', True),
        ])
        self.assertEqual(count, 1, 'No debe haber registros duplicados.')

    def test_rechazar_no_crea_predefinida(self):
        """Rechazar una propuesta NO debe crear ningún registro en
        actividad.tipo.predefinida."""
        antes = self.env['actividad.tipo.predefinida'].search_count([
            ('is_comite', '=', True),
        ])
        propuesta = self._make_propuesta()
        propuesta.write({'motivo_rechazo': 'Rechazado en test.'})
        propuesta.action_rechazar()

        despues = self.env['actividad.tipo.predefinida'].search_count([
            ('is_comite', '=', True),
        ])
        self.assertEqual(antes, despues, 'El rechazo no debe crear predefinidas.')
