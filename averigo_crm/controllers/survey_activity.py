# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class DefaultActivity(http.Controller):
    @http.route('/default_activity_type', type='http', auth='none',
                method=['POST'],
                csrf=False)
    def create_default_activity_type(self, **kw):
        """ Create site survey activity type in every operators"""
        if request.httprequest.method == 'POST':
            operators = request.env['res.company'].sudo().with_context(
                active_test=False).search([])
            for operator in operators:
                default_activity = request.env[
                    'mail.activity.type'].sudo().search(
                    [('name', '=', 'Site Survey'),
                     ('company_id', '=', operator.id)])
                if not default_activity:
                    default_activity_ctx = {
                        'name': 'Site Survey',
                        'company_id': operator.id,
                        'res_model': 'crm.lead',
                    }
                    request.env['mail.activity.type'].sudo().create(
                        default_activity_ctx)
            return "Success"
        else:
            return "Failed"


