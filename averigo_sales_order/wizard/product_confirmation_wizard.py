# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductConfirmation(models.TransientModel):
    """ product confirmation wizard"""
    _name = "product.confirmation"
    _description = 'Product Confirmation'

    name = fields.Char(
        default='Product Confirmation')
    product_ids = fields.Many2many(
        'product.product', string="Product")
    partner_id = fields.Many2one(
        'res.partner', string="Customer")

    def action_confirmation(self):
        """ fun to confirm the wizard action"""
        for product in self.product_ids:
            exist_product_check = self.partner_id.customer_product_ids.mapped(
                'product_id').ids
            exist_product = self.partner_id.product_filter_ids.ids
            product_list = []
            product_uom_lists = []
            if product.id in exist_product_check:
                vals = (0, 0, {
                    'product_id': product.id
                })
                product_uom_lists.append(vals)
            elif product.id not in exist_product:
                dic = {
                    'product_id': product.id,
                    'name': product.name,
                    'product_code': product.default_code,
                    'uom_id': product.uom_id.id,
                    'tax_status': product.tax_status,
                    'item_cost': product.standard_price,
                }
                if self.partner_id.price_category == 'list_price_1':
                    dic.update({
                        'list_price': product.list_price_1,
                    })
                elif self.partner_id.price_category == 'list_price_2':
                    dic.update({
                        'list_price': product.list_price_2,
                    })
                elif self.partner_id.price_category == 'list_price_3':
                    dic.update({
                        'list_price': product.list_price_3,
                    })
                elif not self.partner_id.price_category:
                    dic.update({
                        'list_price': product.list_price,
                    })
                if product.list_price > 0:
                    margin = ((
                                      product.list_price - product.standard_price) / product.list_price) * 100
                    if margin > 0:
                        dic.update({'margin_price': margin,})
                    else:
                        dic.update({'margin_price': 0,})
                else:
                    dic.update(
                        {'margin_price': 0, })
                vals = (0, 0, dic)
                product_list.append(vals)
                self.partner_id.product_filter_ids += product
            self.partner_id.multiple_uom_products = [(2, 0,
                                                      0)] + product_uom_lists
            self.partner_id.customer_product_ids = [(2, 0, 0)] + product_list
