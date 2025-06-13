# -*- coding: utf-8 -*-

from odoo import models, api


class ResCompany(models.Model):
    """ inherits res_company to sale order sequence for new operator"""
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        """ to add sequence for operators"""
        res = super().create(vals_list)
        # create sale order name sequence
        sale_order_ctx = {
            'name': 'Averigo Sequence Sale Order',
            'code': 'sale.order.operator',
            'prefix': 'S',
            'padding': 5,
            'company_id': res.id
        }
        self.env['ir.sequence'].sudo().create([sale_order_ctx])
        # create sale quotation name sequence
        sale_quotation_ctx = {
            'name': 'Averigo Sequence Quotation',
            'code': 'sale.quotation',
            'prefix': 'Q',
            'padding': 5,
            'company_id': res.id
        }
        self.env['ir.sequence'].sudo().create([sale_quotation_ctx])
        sugar_tax_data = {
            'name': 'Sugar Tax',
            'default_code': 'ST00001',
            'product_type': 'service',
            'type': 'service',
            'categ_id': self.env['product.category'].sudo().search(
                [('company_id', '=', res.id)], limit=1).id,
            'company_id': res.id,
            'operator_id': res.id,
            'uom_id': self.env['uom.uom'].sudo().search(
                [('company_id', '=', res.id)], limit=1).id,
            'uom_po_id': self.env['uom.uom'].sudo().search(
                [('company_id', '=', res.id)], limit=1).id,
        }
        self.env['product.template'].with_user(1).create([sugar_tax_data])
        return res

