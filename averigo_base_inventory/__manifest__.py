{
    'name': "Averigo Base Inventory",
    'version': '18.0.1.0.0',
    'description': """
        Averigo Base Inventory
    """,
    'category': 'Purchases',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    # any module necessary for this one to work correctly
        'depends': ['base_averigo', 'product','uom', 'stock_account'],

    # always loaded
    'data': [
        'data/data.xml',
        'data/product_sequence.xml',
        'security/ir.model.access.csv',
        'security/inventory_security.xml',
        'views/product_template_views.xml',
        'views/product_upc_code_views.xml',
        'views/stock_location_view.xml',
        'views/stock_quant_views.xml',
        'views/custom_uom_types_views.xml',
        'views/help_message_views.xml',
        'views/route_route_views.xml',
        'views/product_category_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ]
    },
    'post_init_hook': 'archive_default_categories',
    'uninstall_hook': 'activate_default_categories',
    'license': 'AGPL-3',
}
