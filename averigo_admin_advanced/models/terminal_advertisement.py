# -*- coding: utf-8 -*-
import json
import logging
from urllib.parse import urlparse

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class TerminalAdvertisement(models.Model):
    _name = 'terminal.advertisement'
    _description = 'Terminal Advertisement'
    _rec_name = 'rec'

    rec = fields.Text(
        default='Terminal Advertisement')

    active = fields.Boolean(
        string="Active", default=True)
    operator_ids = fields.Many2many(
        comodel_name='res.company', domain=[('is_main_company', '!=', True)], string="Operator")
    partner_ids = fields.Many2many(
        comodel_name='res.partner', compute='compute_partner_ids')
    location = fields.Many2many(
        comodel_name='res.partner', relation='product_id', column1='partner_id', string='Customer')
    market_ids = fields.Many2many(
        comodel_name='stock.warehouse', compute='compute_micro_market_ids')
    micro_market_id = fields.Many2many(
        comodel_name='stock.warehouse')
    delay_time = fields.Integer(
        default='6')
    local_offer_url = fields.Char(
        string='Local Offers URL')
    product_template_image_ids = fields.One2many(
        comodel_name='advertisement.image', inverse_name='product_tmpl_id', string="Extra Product Media", copy=True)




class AdvertisementImage(models.Model):
    _name = 'advertisement.image'
    _description = "Advertisement Image"
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char(
        string="Name", required=True)
    image_1920 = fields.Image(
        required=True)
    product_tmpl_id = fields.Many2one(
        comodel_name='terminal.advertisement', string="Terminal Template", index=True)

