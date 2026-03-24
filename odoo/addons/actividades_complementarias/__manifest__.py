# -*- coding: utf-8 -*-
{
    'name': 'Actividades Complementarias',
    'version': '19.0.1.1.0',
    'summary': 'Sistema de Créditos Complementarios — ITCH',
    'description': (
        'Gestión integral del ciclo de créditos complementarios del '
        'Instituto Tecnológico de Chetumal. Cubre: propuesta y aprobación '
        'de actividades (JD / Comité Académico), inscripción y seguimiento '
        'de estudiantes, asistencia y evidencias (Responsable de Actividad), '
        'generación y firma dual de constancias, y liberación de créditos '
        '(Servicios Escolares).'
    ),
    'author': 'Desarrollo Institucional',
    'category': 'Education',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/actividades_security.xml',
        'security/ir.model.access.csv',
        'data/tipo_actividad_data.xml',
        'data/estado_actividad_data.xml',
        'data/estado_solicitud_data.xml',
        'data/periodo_data.xml',
        'data/cron_data.xml',
        'views/tipo_actividad_views.xml',
        'views/periodo_views.xml',
        'views/actividad_views.xml',
        'views/propuesta_views.xml',
        'views/empleado_views.xml',
        'views/wizard_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'actividades_complementarias/static/src/scss/style.scss',
        ],
    },
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
