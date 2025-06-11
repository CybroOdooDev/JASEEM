# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class StockQuant(models.Model):
    """Class for the model stock_quant for Inventory Adjustment"""
    _inherit = 'stock.quant'

    stock_inventory_id = fields.Many2one("stock.inventory", string="Inventory")

    product_code = fields.Char(string="Product Code",
                               related="product_id.default_code")

    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'),
         ('confirm', 'In Progress'), ('done', 'Validated')],
        string='Status', default='draft',
        help="Current status of the inventory record.",
        related="stock_inventory_id.state")

    cost = fields.Float(string="Cost", related="product_id.standard_price", )

    current_value = fields.Float(string="Current Value",
                                 compute='_compute_current_value', )

    new_value = fields.Float(string="New Value",
                             compute='_compute_current_value')

    value_difference = fields.Float(string="Value Difference",
                                    compute='_compute_current_value')

    type_id = fields.Many2one("adjust.type", string="Type", )

    def _compute_current_value(self):
        """Compute current value as product cost multiplied by quantity on
        hand."""
        for rec in self:
            cost = rec.product_id.standard_price or 0.0
            rec.current_value = cost * rec.quantity
            rec.new_value = cost * rec.inventory_quantity
            rec.value_difference = rec.new_value - rec.current_value
