# -*- coding: utf-8 -*-
from odoo import fields, models


class UoMChangeHistory(models.Model):
    """Class for the model uom_change_history"""
    _name = "uom.change.history"
    _description = "To record UoM change in Product Master"

    product_id = fields.Many2one(
        'product.template', string="Products")
    category_id = fields.Many2one(
        'product.category', string='Category',
        related="product_id.categ_id", store=1)
    date = fields.Datetime(
        string="Changed Date")
    previous_uom = fields.Many2one(
        'uom.uom', string="Previous UoM")
    changed_uom = fields.Many2one(
        'uom.uom', string="Changed UoM")
    company_id = fields.Many2one(
        'res.company', string="Operator")
    user_id = fields.Many2one(
        'res.users', string="Changed By")
    partner_ids = fields.Many2many(
        'res.partner','partner_ids_uom_change_history',
        string="Associated customers")
