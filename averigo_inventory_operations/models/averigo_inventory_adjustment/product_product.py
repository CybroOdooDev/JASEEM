# -*- coding: utf-8 -*-
from collections import defaultdict
from datetime import datetime
from itertools import product

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """Class to inherit product_product model to add price change functions"""
    _inherit = "product.product"

    def _change_standard_price_update(self, new_price, date,
                                      counterpart_account_id=False):

        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        """Handle stock valuation layers."""
        svl_vals_list = []
        # new_price = max(new_price, 0)
        if 'company_id' in self.env.context:
            company = self.env.context['company_id']
            company_id = self.env['res.company'].browse(company)
        else:
            company_id = self.env.company
        for product in self:
            if product.cost_method not in ('standard', 'average'):
                continue
            quantity_svl = product.with_user(1).quantity_svl
            if float_compare(quantity_svl, 0.0,
                             precision_rounding=product.uom_id.rounding) <= 0:
                continue
            diff = new_price - product.standard_price
            value = company_id.currency_id.round(quantity_svl * diff)
            if company_id.currency_id.is_zero(value):
                continue

            svl_vals = {
                'company_id': company_id.id,
                'product_id': product.id,
                'description': _(
                    'Product value manually modified (from %s to %s)') % (
                                   product.standard_price, new_price),
                'value': value,
                'quantity': 0,
            }
            svl_vals_list.append(svl_vals)
        stock_valuation_layers = self.env[
            'stock.valuation.layer'].with_user(1).create(svl_vals_list)


        """Handle account moves."""
        product_accounts = {
            product.id: product.product_tmpl_id.get_product_accounts() for
            product in self}
        am_vals_list = []
        for stock_valuation_layer in stock_valuation_layers:
            product = stock_valuation_layer.product_id
            value = stock_valuation_layer.value

            if product.type != 'product' or product.valuation != 'real_time':
                continue
            """Sanity check."""
            if counterpart_account_id is False:
                raise UserError(_('You must set a counterpart account.'))
            if not product_accounts[product.id].get('stock_valuation'):
                raise UserError(
                    _('You don\'t have any stock valuation account defined on '
                      'your product category. You must define one before '
                      'processing this operation.'))

            if value < 0:
                debit_account_id = counterpart_account_id
                credit_account_id = product_accounts[product.id][
                    'stock_valuation'].id
            else:
                debit_account_id = product_accounts[product.id][
                    'stock_valuation'].id
                credit_account_id = counterpart_account_id

            move_vals = {
                'journal_id': product_accounts[product.id]['stock_journal'].id,
                'company_id': company_id.id,
                'ref': product.name,
                'stock_valuation_layer_ids': [
                    (6, None, [stock_valuation_layer.id])],
                'line_ids': [(0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (
                        self.env.user.name, product.standard_price, new_price,
                        product.display_name),
                    'account_id': debit_account_id,
                    'debit': abs(value),
                    'credit': 0,
                    'product_id': product.id,
                }), (0, 0, {
                    'name': _('%s changed cost from %s to %s - %s') % (
                        self.env.user.name, product.standard_price, new_price,
                        product.display_name),
                    'account_id': credit_account_id,
                    'debit': 0,
                    'credit': abs(value),
                    'product_id': product.id,
                })],
            }
            am_vals_list.append(move_vals)
        account_moves = self.env['account.move'].create(am_vals_list)
        if account_moves:
            account_moves.post()

        # To create cost tracking record.
        if new_price <= 0 and self.standard_price > 0:
            new_price = self.standard_price

        """Actually update the standard price."""
        _logger.error(
            'product_operator_cost product_cost_change_report '
            '_change_standard_price last')
        _logger.error(self.product_tmpl_id)
        _logger.error(company_id)
        _logger.error(new_price)
        if new_price == 0 and self.standard_price == 0:
            _logger.error(
                'all cost calculation are zero product_cost_change_report '
                '_change_standard_price')

        if new_price != self.standard_price:
            self.env['cost.tracking'].create({'user_id': self.env.user.id,
                                              'product_id': self.product_tmpl_id.id,
                                              'date': date,
                                              'cost': self.standard_price,
                                              'updated_cost': new_price})
            self.env['cost.history'].create({
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'product_id': self.id,
                'product_previous_cost': self.standard_price,
                'product_current_cost': new_price,
                'calculated_cost': new_price,
                'operator_id': self.company_id.id,
                'type_move': 'inventory',
                'user_id': self.env.user.id
            })
        self.with_company(company_id.id).with_user(1).write(
            {'standard_price': new_price})

    # def _run_fifo_vacuum(self, company=None):
    #     """
    #     Function overwritten to avoid cost calculation error when quantity
    #     become negative
    #     """
    #     print(1111111111111111111,self)
    #     if company is None:
    #         company = self.env.company
    #     svls_to_vacuum = self.env['stock.valuation.layer'].with_user(1).search([
    #         ('product_id', '=', self.id),
    #         ('remaining_qty', '<', 0),
    #         ('stock_move_id', '!=', False),
    #         ('company_id', '=', company.id),
    #     ], order='create_date, id')
    #     for product in self:
    #     for svl_to_vacuum in svls_to_vacuum:
    #         domain = [
    #             ('company_id', '=', svl_to_vacuum.company_id.id),
    #             ('product_id', '=', self.id),
    #             ('remaining_qty', '>', 0),
    #             '|',
    #             ('create_date', '>', svl_to_vacuum.create_date),
    #             '&',
    #             ('create_date', '=', svl_to_vacuum.create_date),
    #             ('id', '>', svl_to_vacuum.id)
    #         ]
    #         candidates = self.env['stock.valuation.layer'].with_user(1).search(
    #             domain)
    #         if not candidates:
    #             break
    #         qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
    #         qty_taken_on_candidates = 0
    #         tmp_value = 0
    #         for candidate in candidates:
    #             qty_taken_on_candidate = min(candidate.remaining_qty,
    #                                          qty_to_take_on_candidates)
    #             qty_taken_on_candidates += qty_taken_on_candidate
    #
    #             candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
    #             value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
    #             value_taken_on_candidate = candidate.currency_id.round(
    #                 value_taken_on_candidate)
    #             new_remaining_value = candidate.remaining_value - value_taken_on_candidate
    #
    #             candidate_vals = {
    #                 'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
    #                 'remaining_value': new_remaining_value
    #             }
    #             candidate.write(candidate_vals)
    #
    #             qty_to_take_on_candidates -= qty_taken_on_candidate
    #             tmp_value += value_taken_on_candidate
    #             if float_is_zero(qty_to_take_on_candidates,
    #                              precision_rounding=self.uom_id.rounding):
    #                 break
    #
    #         # Get the estimated value we will correct.
    #         remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
    #         new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
    #         corrected_value = remaining_value_before_vacuum - tmp_value
    #         svl_to_vacuum.write({
    #             'remaining_qty': new_remaining_qty,
    #         })
    #
    #         # Don't create a layer or an accounting entry if the corrected value is zero.
    #         if svl_to_vacuum.currency_id.is_zero(corrected_value):
    #             continue

    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        if company is None:
            company = self.env.company
        ValuationLayer = self.env['stock.valuation.layer'].sudo()
        svls_to_vacuum_by_product = defaultdict(lambda: ValuationLayer)
        res = ValuationLayer._read_group([
            ('product_id', 'in', self.ids),
            ('remaining_qty', '<', 0),
            ('stock_move_id', '!=', False),
            ('company_id', '=', company.id),
        ], ['product_id'], ['id:recordset', 'create_date:min'],
            order='create_date:min')
        min_create_date = datetime.max
        if not res:
            return
        for group in res:
            svls_to_vacuum_by_product[group[0].id] = group[1].sorted(
                key=lambda r: (r.create_date, r.id))
            min_create_date = min(min_create_date, group[2])
        all_candidates_by_product = defaultdict(lambda: ValuationLayer)
        res = ValuationLayer._read_group([
            ('product_id', 'in', self.ids),
            ('remaining_qty', '>', 0),
            ('company_id', '=', company.id),
            ('create_date', '>=', min_create_date),
        ], ['product_id'], ['id:recordset'])
        for group in res:
            all_candidates_by_product[group[0].id] = group[1]

        new_svl_vals_real_time = []
        new_svl_vals_manual = []
        real_time_svls_to_vacuum = ValuationLayer

        for product in self:
            all_candidates = all_candidates_by_product[product.id]
            current_real_time_svls = ValuationLayer
            for svl_to_vacuum in svls_to_vacuum_by_product[product.id]:
                # We don't use search to avoid executing _flush_search and to decrease interaction with DB
                candidates = all_candidates.filtered(
                    lambda r: r.create_date > svl_to_vacuum.create_date
                              or r.create_date == svl_to_vacuum.create_date
                              and r.id > svl_to_vacuum.id
                )
                if not candidates:
                    break
                qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
                qty_taken_on_candidates = 0
                tmp_value = 0
                for candidate in candidates:
                    qty_taken_on_candidate = min(candidate.remaining_qty,
                                                 qty_to_take_on_candidates)
                    qty_taken_on_candidates += qty_taken_on_candidate

                    candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                    value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                    value_taken_on_candidate = candidate.currency_id.round(
                        value_taken_on_candidate)
                    new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                    candidate_vals = {
                        'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                        'remaining_value': new_remaining_value
                    }
                    candidate.write(candidate_vals)
                    if not (candidate.remaining_qty > 0):
                        all_candidates -= candidate

                    qty_to_take_on_candidates -= qty_taken_on_candidate
                    tmp_value += value_taken_on_candidate
                    if float_is_zero(qty_to_take_on_candidates,
                                     precision_rounding=product.uom_id.rounding):
                        break

                # Get the estimated value we will correct.
                remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
                new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
                corrected_value = remaining_value_before_vacuum - tmp_value
                svl_to_vacuum.write({
                    'remaining_qty': new_remaining_qty,
                })

                # Don't create a layer or an accounting entry if the corrected value is zero.
                if svl_to_vacuum.currency_id.is_zero(corrected_value):
                    continue

        #         corrected_value = svl_to_vacuum.currency_id.round(corrected_value)
        #
        #         move = svl_to_vacuum.stock_move_id
        #         new_svl_vals = new_svl_vals_real_time if product.valuation == 'real_time' else new_svl_vals_manual
        #         new_svl_vals.append({
        #             'product_id': product.id,
        #             'value': corrected_value,
        #             'unit_cost': 0,
        #             'quantity': 0,
        #             'remaining_qty': 0,
        #             'stock_move_id': move.id,
        #             'company_id': move.company_id.id,
        #             'description': 'Revaluation of %s (negative inventory)' % (move.picking_id.name or move.name),
        #             'stock_valuation_layer_id': svl_to_vacuum.id,
        #         })
        #         if product.valuation == 'real_time':
        #             current_real_time_svls |= svl_to_vacuum
        #     real_time_svls_to_vacuum |= current_real_time_svls
        # ValuationLayer.create(new_svl_vals_manual)
        # vacuum_svls = ValuationLayer.create(new_svl_vals_real_time)
        #
        # # If some negative stock were fixed, we need to recompute the standard price.
        # for product in self:
        #     product = product.with_company(company.id)
        #     if not svls_to_vacuum_by_product[product.id]:
        #         continue
        #     if product.cost_method in ['average', 'fifo'] and not float_is_zero(product.quantity_svl,
        #                                                               precision_rounding=product.uom_id.rounding):
        #         product.sudo().with_context(disable_auto_svl=True).write({'standard_price': product.value_svl / product.quantity_svl})
        #
        # vacuum_svls._validate_accounting_entries()
        # self._create_fifo_vacuum_anglo_saxon_expense_entries(zip(vacuum_svls, real_time_svls_to_vacuum))
