# -*- coding: utf-8 -*-
from odoo import models, fields


class MicroMarketWarehouse(models.Model):
    """Class for the model stock_warehouse."""
    _name = "stock.warehouse"
    _inherit = ['stock.warehouse', 'mail.thread']
    _description = "Location"
    _order = "name"
    _check_company_auto = True

    def _get_country(self):
        """ Get default country as United States"""
        country = self.env.ref('base.us').id
        return country

    name = fields.Char(
        string='Name', index=True, required=True, default=None, size=50)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer', default=None,
        check_company=True, ondelete='restrict', copy=False)
    partner_name = fields.Char(
        string='Customer/Location', store=True)
    code = fields.Char(
        string='Short Name', required=True, size=50)
    location_id = fields.Char(
        string='Location Id', size=6, copy=False)
    location_type = fields.Selection([
        ('micro_market', 'Micromarket'),
        ('pantry', 'Pantry'),
        ('transit', 'Truck'),
        ('view', 'Warehouse'),
        ('branch', 'Branch')], string='Location Type',
        default='view', index=True, required=True, tracking=True)
    location_type_view = fields.Selection([
        ('micro_market', 'Micromarket'),
        ('pantry', 'Pantry'),
        ('transit', 'Truck'),
        ('view', 'Warehouse'),
        ('branch', 'Branch')], string='Location Type',
        default='view', index=True, required=True, tracking=True, store=True,
        related='location_type')
    street = fields.Char(
        string='Street')
    street2 = fields.Char(
        string='Street2')
    zip = fields.Char(
        string='Zip', size=5)
    city = fields.Char(
        string='City')
    county = fields.Char(
        string='County')
    state_id = fields.Many2one(
        comodel_name='res.country.state', string="State", domain="[('country_id', '=', country_id)]")
    state_name = fields.Char(
        string="State", store=True)
    country_id = fields.Many2one(
        comodel_name='res.country', string="Country", default=_get_country)
    email = fields.Char(
        string='Email', store=True, readonly=False)
    contact_person = fields.Char(
        string='Contact Name', store=True, readonly=False)
    operator_own = fields.Boolean()
    is_parts_warehouse = fields.Boolean(
        'Is Parts Warehouse', help="This is used to separate parts warehouse")