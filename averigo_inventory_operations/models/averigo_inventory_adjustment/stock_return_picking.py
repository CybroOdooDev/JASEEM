# -*- coding: utf-8 -*-
from odoo import fields, api, models, _
from odoo.exceptions import  UserError
import logging

_logger = logging.getLogger(__name__)


class ReturnPicking(models.TransientModel):
    """Extends the `stock.return.picking` model to handle return picking operations with additional functionality."""
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        """super this for updating return qty in return wizard"""
        for rec in self.product_return_moves:
            move_id = self.picking_id.move_ids_without_package.search([
                ('product_id', '=', rec.product_id.id),
                ('picking_id', '=', self.picking_id.id),
                ('id', '=', rec.move_id.id),
                ('product_uom', '=', rec.product_uom_id.id),
                ('state', '=', 'done')])
            if not rec.quantity == 0:
                move_id.return_count += rec.quantity
        new_picking, pick_type_id = super(ReturnPicking,
                                          self)._create_returns()
        picking_id = self.env['stock.picking'].browse(new_picking)
        picking_id.write({
            'return_reason': self.return_reason
        })
        picking_id.is_purchase_return = True
        picking_id.button_validate()
        for line in picking_id.move_line_ids_without_package.filtered(
                lambda l: l.state == 'done'):
            if line.product_id.categ_id.property_cost_method == 'average':
                # Phase 2 - Purchase Order Issue
                if line.product_id.qty > 0:
                    cost = ((
                                    line.product_id.qty + line.qty_done) * line.product_id.standard_price - line.qty_done * line.move_id.cost_price) / (
                               line.product_id.qty)
                else:
                    cost = line.move_id.cost_price / line.move_id.product_uom.factor_inv
                if cost <= 0:
                    cost = line.move_id.cost_price / line.move_id.product_uom.factor_inv
                if cost == 0 and line.move_id.cost_price == 0 and line.product_id.standard_price == 0:
                    _logger.error(
                        'all cost calculation are zero product_cost_change_report _create_returns')

                _logger.error(
                    'cost product_cost_change_report _change_standard_price last')
                _logger.error(cost)
                if line.product_id.standard_price != cost:
                    self.env['cost.history'].create({
                        'date': line.create_date,
                        'product_id': line.product_id.id,
                        'product_previous_cost': line.product_id.standard_price,
                        'product_current_cost': cost,
                        'purchase_id': line.purchase_line_id.order_id.id,
                        'from_location_id': line.location_id.id,
                        'to_location_id': line.location_dest_id.id,
                        'calculated_quantity': line.product_id.qty,
                        'calculated_cost': cost,
                        'operator_id': line.picking_id.company_id.id,
                        'type_move': 'purchase_return',
                        'user_id': self.env.user.id,
                        'move_id': line.move_line_id.id
                    })
                _logger.error(
                    'cost product_cost_change_report _change_standard_price '
                    'last')
                _logger.error(cost)
                line.product_id.standard_price = cost
        return new_picking, pick_type_id
