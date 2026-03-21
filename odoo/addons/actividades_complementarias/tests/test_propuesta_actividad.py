# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('actividades_complementarias', '-standard')
class TestPropuestaActividad(TransactionCase):
    """Tests para el modelo actividad.propuesta.

    Todos los estados se obtienen con env.ref() usando los xmlids definidos
    en los archivos de datos del módulo. Nunca se crean entradas en
    ir.model.data manualmente — el módulo ya las carga al instalarse.
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
        cls.estado_aprobada = cls.env.ref(
            'actividades_complementarias.estado_aprobada'
        )
        cls.estado_rechazada = cls.env.ref(
            'actividades_complementarias.estado_rechazada'
        )

        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Taller Test'})

        hoy = date.today()
        cls.actividad = cls.env['actividad.complementaria'].create({
            'name': 'Actividad para Propuesta',
            'tipo_actividad_id': cls.tipo.id,
            'periodo': '2025-A',
            'fecha_inicio': hoy + timedelta(days=1),
            'fecha_fin': hoy + timedelta(days=2),
            'cantidad_horas': 4.0,
        })

    def _make_propuesta(self, **kwargs):
        """Helper: crea una propuesta con valores mínimos válidos."""
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

    def test_fecha_limite_es_cinco_dias_despues(self):
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
