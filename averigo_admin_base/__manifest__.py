# -*- coding: utf-8 -*-
{
    'name': 'Averigo Admin Base',
    'version': '18.0.1.0.0',
    'summary': 'Admin base module for Averigo',
    'category': 'Administration',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['averigo_base_customer'],
    'data': [
        "security/ir.model.access.csv",
        "views/res_app_users_view.xml",
        "views/ir_image_views.xml",
    ],
    'assets': {
        'web.assets_backend': [

        ]
    },
    'images': [],
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
