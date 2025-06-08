# -*- coding: utf-8 -*-
import threading

from odoo import models, api, fields


class ResCompany(models.Model):
    """class to inherit res_company model"""
    _inherit = 'res.company'

    @api.model_create_multi
    def create(self, vals_list):
        """ Function to create Super company to configure product code sequence and create crv tax"""
        res = super().create(vals_list)
        tax_group = self.env['account.tax.group'].with_user(1).create([{
            'name': 'VAT',
            'company_id': res.id,
        }])
        crv_tax_5 = {
            'name': 'CRV 5 Cents',
            'type_tax_use': 'sale',
            'amount_type': 'fixed',
            'amount': 0.05,
            'active': True,
            'crv': True,
            'description': '5 Cents',
            'company_id': res.id,
            'tax_group_id': tax_group.id,
            'country_id': res.country_id.id,
        }
        self.env['account.tax'].with_user(1).create([crv_tax_5])
        company_uom_category = {
            'name': 'Unit',
            'company_id': res.id,
        }
        new_uom_category = self.env['uom.category'].with_user(1).create([company_uom_category])
        company_uom = {
            'category_id': new_uom_category.id,
            'name': 'Each',
            'uom_type': 'reference',
            'factor': '1.0',
            'company_id': res.id,
        }
        new_uom_uom = self.env['uom.uom'].with_user(1).create([company_uom])
        company_product_category = {
            'name': 'Default Category',
            'company_id': res.id,
        }
        self.env['product.category'].with_user(1).create([company_product_category])
        self.env['ir.sequence'].with_user(1).create([{
            'name': f"Product Code ({res.name})",
            'code': 'product.code.sequence',
            'prefix': 'PT',
            'padding': 5,
            'number_next': 1,
            'number_increment': 1,
            'company_id': res.id,
        }])
        test_mode = getattr(threading.current_thread(), 'testing', False)
        primary_warehouse = False
        if not test_mode:
            primary_warehouse = self.env['stock.warehouse'].with_user(1).create([{
                'name': res.name,
                'code': res.name[:5],
                'company_id': res.id,
                'partner_id': res.partner_id.id,
                'zip': res.zip,
                'street': res.street,
                'city': res.city,
                'county': res.county,
                'location_id': res.name[:5],
            }])
        transit_warehouse = self.env['stock.warehouse'].with_user(1).create([{
            'name': f'{res.name} Transit',
            'code': f'{res.name[:5]} Transit',
            'location_type': 'transit',
            'company_id': res.id,
            'partner_id': res.partner_id.id,
            'zip': res.zip,
            'street': res.street,
            'city': res.city,
            'county': res.county,
            'location_id': f'{res.name[:5]} Transit',
        }])
        res.default_warehouse_id = primary_warehouse.id if primary_warehouse else self.env['stock.warehouse'].sudo().search([('company_id', '=', res.id)],limit=1).id
        return res


class AccountTax(models.Model):
    """class to inherit account_tax model"""
    _inherit = 'account.tax'

    crv = fields.Boolean()
