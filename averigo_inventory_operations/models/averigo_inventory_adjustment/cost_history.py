# -*- coding: utf-8 -*-
from odoo import fields, api, models, _


class CostHistory(models.Model):
    """To store cost history, setup data audit and send mail of zero cost"""
    _name = 'cost.history'
    _description = 'To record cost change history'
    _order = "id desc"





    date = fields.Datetime(
        string='Change Date', help='Date at which cost changed')
    product_id = fields.Many2one(
        'product.product', string='Product', help='Product Name')
    product_previous_cost = fields.Float(
        string='Previous Cost', digits='Product Cost')
    calculated_cost = fields.Float(
        string='Calculated Cost', digits='Product Cost')
    product_current_cost = fields.Float(
        string='Current Cost', digits='Product Cost')
    purchase_id = fields.Many2one(
        'purchase.order', string='Related Purchase Order')
    sale_order_id = fields.Many2one(
        'sale.order', string='Related Sale Order')
    user_id = fields.Many2one(
        'res.user', string='Related User')
    users_id = fields.Many2one(
        'res.users', string='Related User', compute="compute_users")
    from_location_id = fields.Many2one(
        'stock.location', string='From Location',
        help="Location where the products takes from.")
    to_location_id = fields.Many2one(
        'stock.location', string='To Location',
        help="Location where the system will stock the products.")
    calculated_quantity = fields.Float(
        string='Calculated Quantity', default=0.0,
        digits='Product Unit of Measure', copy=False)
    operator_id = fields.Many2one(
        'res.company', 'Operator', help='Corresponding Operator')
    picking_id = fields.Many2one(
        "stock.picking", 'Stock picking')
    value_difference = fields.Float(
        compute="_compute_difference")
    move_id = fields.Many2one(
        "stock.move", 'Stock Move')
    type_move = fields.Selection(
        [('inventory', 'Inventory Adjustment'), ('purchase', 'Purchase'),
         ('sales_return', 'Sales Return'), ('bill', 'Direct Bill'),
         ('receipt', 'Material Receipt'),
         ('purchase_return', 'Purchase Return'),
         ('product_master', 'Product Master')])

    def _compute_difference(self):
        """Function to calculate the difference between two cost histories"""
        for rec in self:
            rec.value_difference = "%.2f" % abs(
                float(rec.product_previous_cost - rec.product_current_cost))

    def compute_users(self):
        """Function to calculate the users based on cost history"""
        self.users_id = []
        for rec in self:
            if rec.user_id.id == 1:
                users_id = self.env['res.users'].with_user(1).search(
                    [('id', '=', rec.user_id.id), ('active', '=', False)])
                rec.users_id = users_id.id
            elif rec.user_id:
                rec.users_id = self.env['res.users'].search(
                    [('id', '=', rec.user_id.id)]).id
            else:
                if rec.purchase_id:
                    rec.users_id = rec.purchase_id.with_user(1).user_id.id
                if rec.picking_id:
                    rec.users_id = rec.picking_id.with_user(1).user_id.id
                if rec.move_id:
                    rec.users_id = rec.move_id.picking_id.with_user(
                        1).user_id.id
