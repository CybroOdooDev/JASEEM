{
    'name': 'Averigo Password Eye Widget',
    'version': '18.0.1.0.0',
    'category': 'Web',
    'summary': 'Password field with eye icon to toggle visibility',
    'description': """
        This module provides a password field widget with an eye icon 
        that allows users to toggle password visibility.
    """,
    'author': 'Averigo',
    'website': 'https://www.averigo.com',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'averigo_password_eye_widget/static/src/js/password_eye_widget.js',
            'averigo_password_eye_widget/static/src/xml/password_eye_widget.xml',
            # 'averigo_password_eye_widget/static/src/css/password_eye_widget.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}