# -*- coding: utf-8 -*-
{
    "name": "AveriGo CRM",
    "summary": "CRM Module For Averigo",
    "version": "18.0.1.0.0",
    "category": "CRM",
    "website": "http://www.cybrosys.com",
    "description": """This module sets up the CRM flow for Averigo.""",
    "author": "Cybrosys Techno Solutions Pvt Ltd.",
    "license": "LGPL-3",
    "depends": [
        "base", "web", "crm", "mail", "survey",
        "averigo_base_customer",
        'odoo_docusign_connector'
    ],
    "data": [
        "data/crm_visitor_types_data.xml",
        "data/crm_stage_data.xml",
        "data/grabscango_site_survey.xml",
        "data/mail_template_data.xml",
        "data/survey_mail_template.xml",
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/crm_lead_views.xml",
        "views/docu_sign_menu.xml",
        "views/sales_team_inherit_views.xml",
        "views/convert_opportunity_wizard.xml",
        "views/mail_activity_type_views.xml",
        "views/survey_inherit_views.xml",
        "views/survey_template_inherit_views.xml",
        "views/transfer_lead_views.xml",
        "views/crm_admin_users_views.xml",
        "views/res_partner_inherit_views.xml",
        "views/activity_events_views.xml",
        "wizard/proposal_action_views.xml",
        "wizard/agreement_action_views.xml",
        "wizard/sow_action_wizard_views.xml",
        "wizard/transfer_wizard_views.xml",
        "views/res_company_views.xml",
    ],
    "assets": {
        "survey.survey_assets": [
            "averigo_crm/static/src/js/surveyformwidget.js",
            "averigo_crm/static/src/js/surveyupload.js",
            "averigo_crm/static/src/scss/survey_template.scss",
        ],
        "web.assets_backend": [
            "averigo_crm/static/src/js/attachment_preview.js",
            "averigo_crm/static/src/js/edit_document.js",
            "averigo_crm/static/src/xml/attachment_preview.xml",
            "averigo_crm/static/src/xml/pdf_viewer_field.xml",
            "averigo_crm/static/src/scss/pdf_viewer_edit.scss",
        ],
        'web.assets_frontend': [

        ]


    },
    "installable": True,
    "application": True,
}
