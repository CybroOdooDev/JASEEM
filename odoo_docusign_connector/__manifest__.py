# -*- coding: utf-8 -*-
{
    'name': 'Odoo Docusign Connector',
    'version': '18.0.1.0.0',
    'summary': 'Integrating Docusign application with odoo',
    'description': """
        This module integrates Docusign functionality with Odoo.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/docusign_config_views.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'external_dependencies': {
        'python': ['docusign_esign'],
    },
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'auto_install': False,
    'category': 'Tools',
}