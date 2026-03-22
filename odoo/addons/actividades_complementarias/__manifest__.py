# -*- coding: utf-8 -*-
{
    'name': 'Actividades Complementarias',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de actividades complementarias para el Jefe de Departamento',
    'description': (
        'Módulo para la gestión de actividades complementarias. '
        'Permite al Jefe de Departamento crear y proponer actividades '
        'al Comité Académico, gestionar su ciclo de vida (aprobación, '
        'asignación, difusión, firma) y delegar permisos a su personal.'
    ),
    'author': 'Desarrollo Institucional',
    'category': 'Education',
    'license': 'LGPL-3',
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
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
