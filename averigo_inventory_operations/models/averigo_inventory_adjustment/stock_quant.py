# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class StockQuant(models.Model):
    """Class for the model stock_quant for Inventory Adjustment"""
    _inherit = 'stock.quant'

    inventory_id = fields.Many2one("stock.inventory", string="Inventory")
