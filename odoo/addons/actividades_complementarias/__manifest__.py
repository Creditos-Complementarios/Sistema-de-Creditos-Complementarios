# -*- coding: utf-8 -*-
{
    'name': 'Actividades Complementarias',
    'version': '19.0.1.0.0',
    'summary': 'Gestión de actividades complementarias para el Jefe de Departamento',
    'description': """
        Módulo para la gestión de actividades complementarias.
        Permite al Jefe de Departamento:
        - Crear y proponer actividades complementarias al Comité Académico.
        - Gestionar el ciclo de vida de las actividades (aprobación, asignación, difusión, firma).
        - Delegar permisos a su personal de departamento.
    """,
    'author': 'Desarrollo Institucional',
    'category': 'Education',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/actividades_security.xml',
        'security/ir.model.access.csv',
        'data/tipo_actividad_data.xml',
        'data/estado_actividad_data.xml',
        'data/estado_solicitud_data.xml',
        'data/cron_data.xml',
        'views/tipo_actividad_views.xml',
        'views/actividad_views.xml',
        'views/propuesta_views.xml',
        'views/empleado_views.xml',
        'views/wizard_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
    'demo': [
        'data/demo_data.xml',
    ],
}
