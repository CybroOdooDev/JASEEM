# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    """product.template is inherit to super write function"""
    _inherit = "product.template"

    name = fields.Char(
        'Product Name', index=True, required=True, translate=True)

    def action_view_cost_changes(self):
        """Function to returns the action to view cost changes for this product."""
        self.ensure_one()
        action = self.env.ref('averigo_inventory_adjustment.action_cost_tracking').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        return action

    def action_view_cost_change_history(self):
        """Fucntion to returns the action to view the cost change history for this product template."""
        self.ensure_one()
        action = self.env.ref(
            'product_cost_change_report.action_cost_history').read()[0]
        product = self.env['product.product'].search(
            [('product_tmpl_id', '=', self.id)], limit=1)
        action['domain'] = [('product_id', '=', product.id),
                            ('value_difference', '>', 0.00)]
        return action
