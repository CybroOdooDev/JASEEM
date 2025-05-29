# -*- coding: utf-8 -*-
from odoo import models, api

class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        for company in res:  # ✅ Loop through each created company
            wh_transfer_ctx = {
                'name': 'Warehouse Transfer Sequence',
                'code': 'virtual.location.transfer',
                'prefix': 'WHT/',
                'padding': 5,
                'company_id': company.id  # ✅ Use the new company's ID
            }
            self.env['ir.sequence'].sudo().create(wh_transfer_ctx)

        return res