# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timezone
from odoo.exceptions import UserError, ValidationError


class FeesDistribution(models.Model):
    _name = 'fees.distribution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fees Distribution"
    _rec_name = 'name'

    name = fields.Char(required=1, tracking=True)
    company_ids = fields.Many2many('res.company')
    micro_market_ids = fields.Many2many('stock.warehouse', tracking=True, copy=False)
    dom_mm_ids = fields.Many2many('stock.warehouse', compute='_compute_dom_mm_ids')
    group_id = fields.Many2one('customer.fees', tracking=True)
    group_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    group_fees_percentage = fields.Float(tracking=True)
    additional_group1_id = fields.Many2one('customer.fees', tracking=True)
    additional_group1_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'),
         ('platform_fees', 'Platform Fees')], tracking=True)
    additional_group1_fees_percentage = fields.Float(tracking=True)
    brand_id = fields.Many2one('customer.fees', tracking=True)
    brand_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    brand_fees_percentage = fields.Float(tracking=True)
    management_id = fields.Many2one('customer.fees', tracking=True)
    management_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    management_fees_percentage = fields.Float(tracking=True)
    national_sales_team_id = fields.Many2one('customer.fees', tracking=True)
    national_sales_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    national_sales_fees_percentage = fields.Float(tracking=True)
    purchasing_group_id = fields.Many2one('customer.fees', tracking=True)
    purchasing_group_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'),
         ('platform_fees', 'Platform Fees')], tracking=True)
    purchasing_group_fees_percentage = fields.Float(tracking=True)
    local_sales_team_id = fields.Many2one('customer.fees', tracking=True)
    local_sales_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    local_sales_fees_percentage = fields.Float(tracking=True)
    cc_fees = fields.Float(tracking=True)
    app_fees = fields.Float(tracking=True)
    stored_fund_fees = fields.Float(tracking=True)
    platform_fees = fields.Float(tracking=True)
    platform_fees_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')], required=True, default='percentage')
    platform_fees_per_day = fields.Float(store=1,
                                         compute="_compute_platform_fees_per_day")
    room_cc = fields.Float('Hotel CC', tracking=True)
    cash_adj = fields.Float(tracking=True)

    @api.depends('company_ids')
    def _compute_dom_mm_ids(self):
        """Compute available micro market IDs excluding those already in use."""
        # Batch fetch existing micro market IDs to avoid N+1 queries
        existing_mm_ids = self.env['fees.distribution'].search([
            ('id', 'not in', self.ids)]).mapped('micro_market_ids')
        for record in self:
            record.dom_mm_ids = False
            if record.company_ids:
                domain = [
                    ('company_id', 'in', record.company_ids.ids),
                    ('location_type', '=', 'micro_market')]
            else:
                domain = [
                    ('company_id.active', '=', True),
                    ('location_type', '=', 'micro_market')]
            all_mm_ids = self.env['stock.warehouse'].sudo().search(domain)
            available_mm_ids = all_mm_ids - existing_mm_ids
            record.dom_mm_ids = available_mm_ids

    @api.depends('platform_fees', 'platform_fees_type')
    def _compute_platform_fees_per_day(self):
        print(self,"sle")
        for rec in self:
            rec.platform_fees_per_day = (rec.platform_fees * 12) / 365 if (
                    rec.platform_fees_type == 'fixed') else 0

    def update_micromarket(self):
        view = self.env.ref('averigo_admin_advanced.fees_location_update_view_form')
        wiz = self.env['fees.location.update'].create(
            {'micro_market_ids': self._origin.micro_market_ids.ids,
             'fees_template_id': self._origin.id})
        return {
            'name': _('Update Micromarket Fees'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'fees.location.update',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

