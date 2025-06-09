# -*- coding: utf-8 -*-
{
    'name': 'Averigo Admin Advanced',
    'version': '18.0.1.0.0',
    'category': '',
    'summary': 'Base Module For Averigo Admin Advanced Setup',
    'description': """This module setups the Advanced Admin Setup""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['averigo_admin_base', 'averigo_micro_market'],
    'data': [
        'data/sequence.xml',
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/user_session_history_views.xml',
        'views/terminal_advertisement.xml',
        'views/employee_discount_setup_views.xml',
        'views/mobile_notification_views.xml',
        'views/admin_featured_products_views.xml',
        'views/upc_scan_failure_views.xml',
        'views/customer_fees_views.xml',
        'views/customer_fees_type_views.xml',
        'views/fees_distribution_views.xml',
        'views/stock_warehouse_views.xml',
        'wizard/fees_location_update_views.xml',
        'wizard/transaction_fees_update_views.xml'
    ],
    'assets': {
        'web.assets_backend': [

        ],
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}