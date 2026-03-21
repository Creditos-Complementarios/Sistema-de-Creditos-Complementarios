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

        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Taller'})

        cls.estado_aprobada = cls.env['actividad.estado'].create({
            'name': 'Aprobada', 'code': 'aprobada',
        })
        cls.estado_rechazada = cls.env['actividad.estado'].create({
            'name': 'Rechazada', 'code': 'rechazada',
        })

        cls.estado_sol_en_revision = cls.env['actividad.estado.solicitud'].create({
            'name': 'En Revisión', 'code': 'en_revision',
        })
        cls.estado_sol_aprobada = cls.env['actividad.estado.solicitud'].create({
            'name': 'Aprobada', 'code': 'aprobada',
        })
        cls.estado_sol_rechazada = cls.env['actividad.estado.solicitud'].create({
            'name': 'Rechazada', 'code': 'rechazada',
        })

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
        """Aprobar una propuesta debe actualizar estado de propuesta y actividad."""
        propuesta = self._make_propuesta()
        # Patch env.ref to return our test records
        self.env['ir.model.data'].create([
            {
                'name': 'estado_solicitud_aprobada',
                'module': 'actividades_complementarias',
                'model': 'actividad.estado.solicitud',
                'res_id': self.estado_sol_aprobada.id,
            },
            {
                'name': 'estado_aprobada',
                'module': 'actividades_complementarias',
                'model': 'actividad.estado',
                'res_id': self.estado_aprobada.id,
            },
        ])
        propuesta.action_aprobar()
        self.assertEqual(propuesta.estado_solicitud_id, self.estado_sol_aprobada)
        self.assertEqual(propuesta.actividad_id.estado_id, self.estado_aprobada)

    def test_action_rechazar_sin_motivo_falla(self):
        """Rechazar sin motivo debe lanzar ValidationError."""
        propuesta = self._make_propuesta()
        with self.assertRaises(ValidationError):
            propuesta.action_rechazar()

    def test_action_rechazar_con_motivo_ok(self):
        """Rechazar con motivo debe actualizar los estados correctamente."""
        propuesta = self._make_propuesta()
        self.env['ir.model.data'].create([
            {
                'name': 'estado_solicitud_rechazada',
                'module': 'actividades_complementarias',
                'model': 'actividad.estado.solicitud',
                'res_id': self.estado_sol_rechazada.id,
            },
            {
                'name': 'estado_rechazada',
                'module': 'actividades_complementarias',
                'model': 'actividad.estado',
                'res_id': self.estado_rechazada.id,
            },
        ])
        propuesta.write({'motivo_rechazo': 'No cumple los requisitos mínimos.'})
        propuesta.action_rechazar()
        self.assertEqual(propuesta.estado_solicitud_id, self.estado_sol_rechazada)
        self.assertEqual(propuesta.actividad_id.estado_id, self.estado_rechazada)
