# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import ValidationError


class Route(models.Model):
    """To create Route"""
    _name = "route.route"
    _description = 'Delivery Route'

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = self.env.company.default_warehouse_id or self.env[
            'stock.warehouse'].search([('location_type', '=', 'view')], limit=1)
        return warehouse_id

    name = fields.Char()
    desc = fields.Char()
    truck_id = fields.Many2one(
        'stock.warehouse', domain="[('location_type', '=', 'transit')]")
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Warehouse',
        domain="[('location_type', '=', 'view')]",
        default=_default_warehouse_id)
    company_id = fields.Many2one(
        'res.company', string='Operator', index=True,
        default=lambda s: s.env.company,
        readonly=True)

    def unlink(self):
        for record in self:
            rec_id = self.env['res.partner'].search(
                [('route_id', 'in', record.ids)])
            if rec_id:
                raise ValidationError(
                    "You cannot delete this Route because it is linked to one or more Customers.")
            rec_id = self.env['sale.order'].search(
                [('route_id', 'in', record.ids)])
            if rec_id:
                raise ValidationError(
                    "You cannot delete this Route because it is linked to one or more Sales Orders.")
        return super(Route, self).unlink()
