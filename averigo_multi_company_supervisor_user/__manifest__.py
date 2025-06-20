# -*- coding: utf-8 -*-
{
    "name": "Averigo Multi Company Supervisor User",
    'version': '18.0.1.0.0',
    "author": "Cybrosys Techno Solutions",
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    "summary": "Averigo Multi Company Supervisor User Management",
    "description":"Multi Company Supervisor User Management",
    "category": "Generic Modules",
	'images': [],
    "depends": [ "averigo_equipment_management", "averigo_crm"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_users_views.xml",
        "views/supervisor_menus.xml",
      ],
    "assets": {
        "web.assets_backend": [
        ],
    },
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}