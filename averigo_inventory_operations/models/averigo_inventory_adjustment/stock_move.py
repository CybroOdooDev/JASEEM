# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import fields, api, models
from odoo.tools import float_is_zero, float_round

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    """stock.move is inherited to override product_price_update_before_done function"""
    _inherit = "stock.move"

    product_value = fields.Float(digits='Product Value')

    def _should_force_price_unit(self):
        """Determines whether the price unit should be forced to a specific value."""
        self.ensure_one()
        return False

    def _get_price_unit(self):
        """ Returns the unit price to value this stock move """
        self.ensure_one()
        if self.purchase_line_id and self.product_id.id == self.purchase_line_id.product_id.id:
            price_unit_prec = self.env['decimal.precision'].precision_get(
                'Product Price')
            line = self.purchase_line_id
            order = line.order_id
            price_unit = line.price_unit
            if line.taxes_id:
                qty = line.product_qty or 1
                price_unit = \
                    line.taxes_id.with_context(round=False).compute_all(
                        price_unit,
                        currency=line.order_id.currency_id,
                        quantity=qty)[
                        'total_void']
                price_unit = float_round(price_unit / qty,
                                         precision_digits=price_unit_prec)
            if line.product_uom.id != line.product_id.uom_id.id:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
            if order.currency_id != order.company_id.currency_id:
                # The date must be today, and not the date of the move since the move move is still
                # in assigned state. However, the move date is the scheduled date until move is
                # done, then date of actual move processing. See:
                # https://github.com/odoo/odoo/blob/2f789b6863407e63f90b3a2d4cc3be09815f7002/addons/stock/models/stock_move.py#L36
                price_unit = order.currency_id._convert(
                    price_unit, order.company_id.currency_id, order.company_id,
                    fields.Date.context_today(self), round=False)
            return price_unit
        if self.cost_price:
            price_unit = self.cost_price or self.price_unit
            _logger.info('price_unit _get_price_unit if')
            _logger.info(self.product_id)
            _logger.info(self.company_id)
            _logger.info(price_unit)
        else:
            price_unit = self.price_unit
            _logger.info('price_unit _get_price_unit else')
            _logger.info(self.product_id)
            _logger.info(self.company_id)
            _logger.info(price_unit)
        precision = self.env['decimal.precision'].precision_get(
            'Product Price')
        # If the move is a return, use the original move's price unit.
        if self.origin_returned_move_id and self.origin_returned_move_id.with_user(
                1).stock_valuation_layer_ids:
            layers = self.origin_returned_move_id.with_user(
                1).stock_valuation_layer_ids
            quantity = sum(layers.mapped("quantity"))
            return layers.currency_id.round(
                sum(layers.mapped("value")) / quantity) if not float_is_zero(
                quantity, precision_rounding=layers.uom_id.rounding) else 0
        _logger.info('product_operator_cost _get_price_unit before return')
        _logger.info(price_unit)
        _logger.info(float_is_zero(price_unit, precision))
        _logger.info(self._should_force_price_unit())
        _logger.info(self.product_id.standard_price)
        return price_unit if not float_is_zero(price_unit,
                                               precision) or self._should_force_price_unit() else self.product_id.standard_price

    def product_price_update_before_done(self, forced_qty=None):
        """Override already existing function to record cost changes"""
        if self.location_dest_id.warehouse_id.location_type != 'micro_market':
            tmpl_dict = defaultdict(lambda: 0.0)
            # adapt standard price on incoming moves if the product cost_method
            # is 'average'
            std_price_update = {}
            for move in self.filtered(
                    lambda moves: moves._is_in() and moves.with_company(
                        moves.company_id.id).product_id.cost_method == 'average'):
                product_tot_qty_available = move.product_id.with_user(
                    1).with_company(move.company_id.id).qty + tmpl_dict[
                                                move.product_id.id]
                rounding = move.product_id.uom_id.rounding

                # unit_cost = move._get_price_unit() / move.product_uom.factor_inv
                move_cost = move._get_price_unit()
                valued_move_lines = move._get_in_move_lines()
                _logger.error('move_cost_price')
                _logger.error(move.cost_price)
                if move.product_id.uom_id != move.product_uom:
                    unit_cost = move.cost_price / move.product_uom.factor_inv
                else:
                    unit_cost = move_cost
                qty_done = 0
                # Get the standard price
                amount_unit = std_price_update.get((move.company_id.id,
                                                    move.product_id.id)) or move.product_id.with_company(
                    move.company_id.id).standard_price
                calculated_cost = 0
                for valued_move_line in valued_move_lines:
                    qty_done += valued_move_line.product_uom_id._compute_quantity(
                        valued_move_line.qty_done, move.product_id.uom_id)

                qty = forced_qty or qty_done
                if float_is_zero(product_tot_qty_available,
                                 precision_rounding=rounding):
                    new_std_price = unit_cost
                    _logger.error(new_std_price)

                elif float_is_zero(
                        product_tot_qty_available + move.product_qty,
                        precision_rounding=rounding) or \
                        float_is_zero(product_tot_qty_available + qty,
                                      precision_rounding=rounding):
                    new_std_price = unit_cost
                    _logger.error(new_std_price)
                else:
                    # Phase 2 - Purchase Order Issue
                    if product_tot_qty_available <= 0:
                        new_std_price = unit_cost
                    elif (product_tot_qty_available + qty) != 0:
                        _logger.error('calculation_data_average_purchase')
                        _logger.error(amount_unit)
                        _logger.error(product_tot_qty_available)
                        # _logger.error(move._get_price_unit())
                        _logger.error(qty)
                        _logger.error(unit_cost)
                        new_std_price = ((
                                                 amount_unit * product_tot_qty_available) + (
                                                 unit_cost * qty)) / (
                                                product_tot_qty_available + qty) if product_tot_qty_available > 0 else unit_cost
                    else:
                        new_std_price = unit_cost
                if new_std_price <= 0:
                    new_std_price = unit_cost
                if new_std_price == 0 and unit_cost == 0 and amount_unit == 0:
                    _logger.error(
                        'all cost calculation are zero product_price_update_before_done product_cost_change_report')
                _logger.error(
                    'new_std_price product_price_update_before_done 1')
                _logger.error(new_std_price)
                quantity = move.purchase_line_id.product_uom_qty
                old_quantity = move.purchase_line_id.product_id.with_context(
                    location_id=move.location_dest_id.id,
                    to_date=move.date).qty_available or 0
                calculated_quantity = old_quantity + quantity
                order_cost = move.purchase_line_id.price_unit
                product_cost = move.purchase_line_id.product_id.standard_price
                if calculated_quantity:
                    calculated_cost = ((old_quantity * product_cost) + (
                            quantity * order_cost)) / calculated_quantity
                picking_type_name = ''
                if move.location_dest_id.usage == 'inventory' or move.location_id.usage == 'inventory':
                    picking_type_name = 'inventory'
                elif move.location_id.usage == 'supplier':
                    if move.picking_id.purchase_id and not move.picking_id.material_receipt:
                        picking_type_name = 'purchase'
                    elif not move.picking_id.purchase_id and move.picking_id.material_receipt:
                        picking_type_name = 'receipt'
                    else:
                        picking_type_name = 'bill'
                elif move.location_dest_id.usage == 'supplier':
                    picking_type_name = 'purchase_return'
                elif move.location_id.usage == 'customer':
                    picking_type_name = 'sales_return'
                # To record cost changes in cost.history model
                if amount_unit != new_std_price:
                    x = self.env['cost.history'].create({
                        'date': move.date,
                        'product_id': move.product_id.id,
                        'product_previous_cost': amount_unit,
                        'product_current_cost': new_std_price,
                        'purchase_id': move.purchase_line_id.order_id.id,
                        'from_location_id': move.location_id.id,
                        'to_location_id': move.location_dest_id.id,
                        'calculated_quantity': calculated_quantity,
                        'calculated_cost': calculated_cost,
                        'operator_id': move.company_id.id,
                        'type_move': picking_type_name,
                        'user_id': self.env.user.id,
                        'move_id': move.id
                    })
                    _logger.error(x)

                tmpl_dict[move.product_id.id] += qty_done
                # Write the standard price, as SUPERUSER_ID because a warehouse
                # manager may not have the right to write on products
                _logger.error(
                    'new_std_price product_price_update_before_done last')
                _logger.error(new_std_price)
                _logger.error(new_std_price)
                move.product_id.with_company(move.company_id.id).with_user(
                    1).write(
                    {
                        'standard_price': new_std_price})
                std_price_update[
                    move.company_id.id, move.product_id.id] = new_std_price

    @api.onchange("product_uom", "product_uom_qty")
    def _onchange_product_uom(self):
        """Updates the cost price and product value when the product unit of measure or quantity changes."""
        if self.product_uom:
            _logger.error('cost_calculation_averigo '
                          'product_cost_change_report_7')
            _logger.error(
                self.product_id.standard_price * self.product_uom.factor_inv)
            self.cost_price = (
                    self.product_id.standard_price * self.product_uom.factor_inv)
            self.product_value = self.cost_price * self.product_uom_qty
