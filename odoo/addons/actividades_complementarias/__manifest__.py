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
    'depends': ['base', 'mail', 'hr'],
    'data': [
        # 1. Grupos de seguridad (primero siempre)
        'security/actividades_security.xml',
        # 2. Permisos de modelos existentes (CSV — solo modelos ya conocidos)
        'security/ir.model.access.csv',
        # 3. Catálogos SII (deben cargarse antes que datos de actividades)
        'data/01_departamentos.xml',
        'data/02_carreras.xml',
        'data/03_tipousuario.xml',
        'data/04_empleados.xml',
        'data/05_periodos.xml',
        'data/06_estudiantes.xml',
        'data/07_usuarios_sii.xml',
        # 4. Datos del módulo
        'data/tipo_actividad_data.xml',
        'data/tipo_predefinida_data.xml',
        'data/estado_actividad_data.xml',
        'data/estado_solicitud_data.xml',
        'data/cron_data.xml',
        # 5. Vistas
        'views/tipo_actividad_views.xml',
        'views/tipo_predefinida_views.xml',
        'views/periodo_views.xml',
        'views/actividad_views.xml',
        'views/propuesta_views.xml',
        'views/empleado_views.xml',
        'views/wizard_views.xml',
        'views/menu_views.xml',
        # 6. Permisos de los modelos SII nuevos (XML al final, cuando ir.model ya los registró)
        'security/sii_model_access.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'actividades_complementarias/static/src/scss/style.scss',
            'actividades_complementarias/static/src/xml/dark_mode_switch.xml',
            'actividades_complementarias/static/src/js/dark_mode_switch.js',

        ],
    },
    'demo': [
        'data/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
