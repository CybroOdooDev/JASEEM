# -*- coding: utf-8 -*-
{
    'name': 'Averigo Theme',
    'version': '18.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['web', 'base_setup'],
    'data': [
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('after', 'web/static/src/scss/primary_variables.scss', 'averigo_theme/static/src/**/*.variables.scss'),
            ('replace', 'web/static/src/scss/primary_variables.scss', 'averigo_theme/static/src/scss/primary_variables.scss'),
        ],
        'web._assets_secondary_variables': [
            ('before', 'web/static/src/scss/secondary_variables.scss', 'averigo_theme/static/src/scss/secondary_variables.scss'),
        ],
        'web._assets_backend_helpers': [
            ('before', 'web/static/src/scss/bootstrap_overridden.scss', 'averigo_theme/static/src/scss/bootstrap_overridden.scss'),
        ],
        'web.assets_frontend': [
            'averigo_theme/static/src/webclient/home_menu/home_menu_background.scss', # used by login page
            'averigo_theme/static/src/webclient/navbar/navbar.scss',
        ],
        'web.assets_backend': [
            'averigo_theme/static/src/xml/control_panel_template_inherit.xml',
            'averigo_theme/static/src/scss/theme.scss',
            'averigo_theme/static/src/webclient/**/*.scss',
            'averigo_theme/static/src/views/**/*.scss',

            'averigo_theme/static/src/core/**/*',
            'averigo_theme/static/src/webclient/**/*.js',
            ('after', 'web/static/src/views/list/list_renderer.xml', 'averigo_theme/static/src/views/list/list_renderer_desktop.xml'),
            'averigo_theme/static/src/webclient/**/*.xml',
            'averigo_theme/static/src/views/**/*.js',
            'averigo_theme/static/src/views/**/*.xml',
            ('remove', 'averigo_theme/static/src/views/pivot/**'),

            # Don't include dark mode files in light mode
            ('remove', 'averigo_theme/static/src/**/*.dark.scss'),
        ],
        'web.assets_backend_lazy': [
            'averigo_theme/static/src/views/pivot/**',
        ],
        'web.assets_backend_lazy_dark': [
            ('include', 'web.dark_mode_variables'),
            # web._assets_backend_helpers
            ('before', 'averigo_theme/static/src/scss/bootstrap_overridden.scss', 'averigo_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'averigo_theme/static/src/scss/bs_functions_overridden.dark.scss'),
        ],
        'web.assets_web': [
            ('replace', 'web/static/src/main.js', 'averigo_theme/static/src/main.js'),
        ],
        # ========= Dark Mode =========
        "web.dark_mode_variables": [
            # web._assets_primary_variables
            ('before', 'averigo_theme/static/src/scss/primary_variables.scss', 'averigo_theme/static/src/scss/primary_variables.dark.scss'),
            ('before', 'averigo_theme/static/src/**/*.variables.scss', 'averigo_theme/static/src/**/*.variables.dark.scss'),
            # web._assets_secondary_variables
            ('before', 'averigo_theme/static/src/scss/secondary_variables.scss', 'averigo_theme/static/src/scss/secondary_variables.dark.scss'),
        ],
        "web.assets_web_dark": [
            ('include', 'web.dark_mode_variables'),
            # web._assets_backend_helpers
            ('before', 'averigo_theme/static/src/scss/bootstrap_overridden.scss', 'averigo_theme/static/src/scss/bootstrap_overridden.dark.scss'),
            ('after', 'web/static/lib/bootstrap/scss/_functions.scss', 'averigo_theme/static/src/scss/bs_functions_overridden.dark.scss'),
            # assets_backend
            'averigo_theme/static/src/**/*.dark.scss',
        ],
    },
    'license': 'LGPL-3',
    "images":["static/description/img.png"],
}
