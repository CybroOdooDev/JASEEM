# -*- coding: utf-8 -*-
from odoo import fields, models


class CustomerOrderType(models.Model):
    """ model for customer order types"""
    _name = "order.type"
    _description = "Order Type"

    name = fields.Char()
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

