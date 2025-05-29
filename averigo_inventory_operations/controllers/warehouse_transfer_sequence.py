# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response


class WarehouseUpdateController(http.Controller):
    @http.route('/wh_transfer_sequence', type='http', auth='none', method=['POST'], csrf=False)
    def create_wh_transfer_sequence(self, **kw):
        """ To Create warehouse transfer sequence in operators"""
        if request.httprequest.method == 'POST':
            operators = request.env['res.company'].sudo().with_context(active_test=False).search([])
            for operator in operators:
                wh_transfer_sequence = request.env['ir.sequence'].sudo().search(
                    [('code', '=', 'virtual.location.transfer'),
                     ('company_id', '=', operator.id)])
                if not wh_transfer_sequence:
                    wh_transfer_ctx = {
                        'name': 'Warehouse Transfer Sequence',
                        'code': 'virtual.location.transfer',
                        'prefix': 'WHT/',
                        'padding': 5,
                        'company_id': operator.id
                    }
                    request.env['ir.sequence'].sudo().create(wh_transfer_ctx)
            return "Success"
        else:
            return "Failed"
