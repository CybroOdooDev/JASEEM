# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class ResPartnerInherit(models.Model):
    """inherit res partner model for associating products"""
    _inherit = 'res.partner'

    sale_order_count = fields.Integer(
        string="Sale Order Count", compute='_compute_sale_order_count',
        groups='sales_team.group_sale_salesman,'
               'base_averigo.averigo_operator_user_group')

    def unlink(self):
        """ unlink action for customer"""
        sale_order = self.env['sale.order'].sudo().search(
            ['|', '|', ('partner_id', 'in', self.ids),
             ('partner_invoice_id', 'in', self.ids),
             ('partner_shipping_id', 'in', self.ids)])
        if sale_order:
            raise UserError(
                _('You cannot delete the Customer. There is Sale order associated with the Customer / Billing Address / Delivery Address'))
        return super(ResPartnerInherit, self).unlink()

    def _compute_sale_order_count(self):
        """ overrides addon function to return sale_order count for all group users"""
        self.sale_order_count = 0
        # retrieve all children partners and prefetch 'parent_id' on them
        all_partners = self.with_context(active_test=False).search_fetch(
            [('id', 'child_of', self.ids)],
            ['parent_id'],)
        sale_order_groups = self.env['sale.order']._read_group(
            domain=expression.AND([self._get_sale_order_domain_count(), [('partner_id', 'in', all_partners.ids)]]),
            groupby=['partner_id'], aggregates=['__count'])
        self_ids = set(self._ids)
        for partner, count in sale_order_groups:
            while partner:
                if partner.id in self_ids:
                    partner.sale_order_count += count
                partner = partner.parent_id

    def action_view_partner_sale_orders(self):
        """Function for smart button sale orders in customer care"""
        self.ensure_one()
        action = self.env.ref(
                'averigo_sales_order.action_sale_order_customer').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        return action
