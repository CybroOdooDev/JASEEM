{
    'name': "Averigo Inventory Operations",
    'version': '18.0.1.0.0',
    'description': """
        Averigo Base Inventory
    """,
    'category': 'Inventory',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['averigo_base_inventory'],

    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/virtual_location_transfer.xml',
        'views/cost_history_views.xml',
        'views/inventory_adjustment_views.xml',
        'views/value_adjustment_views.xml',
    ],
    'assets': {
        'web.assets_backend': [

        ]
    },
    'license': 'AGPL-3',
}
