# -*- coding: utf-8 -*-
from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('actividades_complementarias', '-standard')
class TestActividad(TransactionCase):
    """Tests para el modelo actividad.complementaria."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Estado mínimo necesario para operar
        cls.tipo = cls.env['actividad.tipo'].create({'name': 'Conferencia'})
        cls.estado_aprobada = cls.env['actividad.estado'].create({
            'name': 'Aprobada',
            'code': 'aprobada',
        })
        cls.estado_finalizada = cls.env['actividad.estado'].create({
            'name': 'Finalizada',
            'code': 'finalizada',
        })

        cls.hoy = date.today()
        cls.manana = cls.hoy + timedelta(days=1)
        cls.pasado_manana = cls.hoy + timedelta(days=2)

    def _make_actividad(self, **kwargs):
        """Helper: crea una actividad con valores mínimos válidos."""
        vals = {
            'name': 'Actividad de prueba',
            'tipo_actividad_id': self.tipo.id,
            'periodo': '2025-A',
            'fecha_inicio': self.manana,
            'fecha_fin': self.pasado_manana,
            'cantidad_horas': 8.0,
            'cupo_min': 5,
            'cupo_max': 30,
        }
        vals.update(kwargs)
        return self.env['actividad.complementaria'].create(vals)

    # ── Constraints ──────────────────────────────────────────────────────────

    def test_fecha_inicio_pasada_falla(self):
        """No se debe poder crear una actividad con fecha de inicio en el pasado."""
        with self.assertRaises(ValidationError):
            self._make_actividad(fecha_inicio=self.hoy - timedelta(days=1))

    def test_fecha_fin_antes_de_inicio_falla(self):
        """La fecha de fin debe ser posterior a la fecha de inicio."""
        with self.assertRaises(ValidationError):
            self._make_actividad(fecha_inicio=self.manana, fecha_fin=self.manana)

    def test_cupo_min_cero_falla(self):
        """El cupo mínimo debe ser al menos 1."""
        with self.assertRaises(ValidationError):
            self._make_actividad(cupo_min=0)

    def test_cupo_max_menor_que_min_falla(self):
        """El cupo máximo no puede ser menor que el mínimo."""
        with self.assertRaises(ValidationError):
            self._make_actividad(cupo_min=10, cupo_max=5)

    def test_cupo_ilimitado_omite_validacion_cupos(self):
        """Con cupo_ilimitado=True no se validan min/max."""
        # No debe lanzar excepción aunque cupo_min=0 y cupo_max=0
        actividad = self._make_actividad(cupo_ilimitado=True, cupo_min=0, cupo_max=0)
        self.assertTrue(actividad.cupo_ilimitado)

    def test_nombre_duplicado_mismo_periodo_falla(self):
        """No puede haber dos actividades activas con el mismo nombre en el mismo periodo."""
        self._make_actividad(name='Actividad Única', estado_id=self.estado_aprobada.id)
        with self.assertRaises(ValidationError):
            self._make_actividad(name='Actividad Única', estado_id=self.estado_aprobada.id)

    def test_nombre_duplicado_diferente_periodo_ok(self):
        """El mismo nombre en diferente periodo sí es válido."""
        self._make_actividad(name='Actividad Repetida', periodo='2025-A')
        # No debe lanzar excepción
        actividad2 = self._make_actividad(name='Actividad Repetida', periodo='2025-B')
        self.assertTrue(actividad2.id)

    # ── Business logic ───────────────────────────────────────────────────────

    def test_action_enviar_catalogo_estado_invalido_falla(self):
        """No se puede enviar al catálogo una actividad que no está aprobada."""
        actividad = self._make_actividad()  # sin estado
        with self.assertRaises(ValidationError):
            actividad.action_enviar_catalogo()

    def test_action_enviar_catalogo_estado_aprobado_ok(self):
        """Una actividad aprobada se puede enviar al catálogo."""
        actividad = self._make_actividad(estado_id=self.estado_aprobada.id)
        actividad.action_enviar_catalogo()
        self.assertTrue(actividad.en_catalogo)

    def test_action_firmar_constancias_requiere_finalizada(self):
        """No se pueden firmar constancias de una actividad no finalizada."""
        actividad = self._make_actividad(estado_id=self.estado_aprobada.id)
        with self.assertRaises(ValidationError):
            actividad.action_firmar_constancias()

    def test_action_firmar_constancias_finalizada_ok(self):
        """Una actividad finalizada puede tener constancias firmadas."""
        actividad = self._make_actividad(estado_id=self.estado_finalizada.id)
        actividad.action_firmar_constancias()
        self.assertTrue(actividad.constancias_firmadas)

    # ── Computes ─────────────────────────────────────────────────────────────

    def test_alumno_count_compute(self):
        """El contador de alumnos debe reflejar los registros en Many2many."""
        actividad = self._make_actividad()
        self.assertEqual(actividad.alumno_count, 0)

        partner1 = self.env['res.partner'].create({'name': 'Alumno 1'})
        partner2 = self.env['res.partner'].create({'name': 'Alumno 2'})
        actividad.write({'alumno_ids': [(4, partner1.id), (4, partner2.id)]})
        self.assertEqual(actividad.alumno_count, 2)
