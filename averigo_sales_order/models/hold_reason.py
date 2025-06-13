# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderHold(models.Model):
    """ class to define hold reason """
    _name = "hold.reason"
    _description = 'Hold Reason'

    name = fields.Char()
    company_id = fields.Many2one(
        'res.company', string='Operator', index=True, default=lambda s: s.env.company.id)


class SaleOrderClosed(models.Model):
    """ class to define closed reason"""
    _name = "closed.reason"
    _description = 'Closed Reason'

    name = fields.Char()
    company_id = fields.Many2one(
        'res.company', string='Operator', index=True,
        default=lambda s: s.env.company.id)


class DropOffLocation(models.Model):
    """Drop Location"""
    _name = "drop.location"
    _description = 'Drop Off Location'
    _rec_name = 'desc'

    company_id = fields.Many2one(
        'res.company', string='Operator', index=True,
        default=lambda s: s.env.company.id)
    code = fields.Char(
        'Code')
    desc = fields.Char(
        'Location')
    note = fields.Text()
