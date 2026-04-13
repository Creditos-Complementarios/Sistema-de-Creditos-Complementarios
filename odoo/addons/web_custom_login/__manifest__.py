{
    'name': 'Custom Login',
    'version': '19.0.1.0.0',
    'depends': ['web'],
    'data': ['views/login_custom.xml'],
    'assets': {
        'web.assets_frontend': [
            'web_custom_login/static/src/css/login_custom.css',
        ],
    },
    'installable': True,
    'license': 'LGPL-3',
}
