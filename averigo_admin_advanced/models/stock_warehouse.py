# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    fees_template_id = fields.Many2one('fees.distribution')
    cc_fees = fields.Float(tracking=True)
    app_fees = fields.Float(tracking=True)
    stored_fund_fees = fields.Float(tracking=True)
    platform_fees = fields.Float(tracking=True)
    platform_fees_type = fields.Selection(
        [('percentage', 'Percentage'), ('fixed', 'Fixed')], required=True,
        default='percentage')
    platform_fees_per_day = fields.Float()
    room_cc = fields.Float('Hotel CC', tracking=True)
    cash_adj = fields.Float(tracking=True)
    group_id = fields.Many2one('customer.fees', string='Hotel Commission',
                               tracking=True)
    group_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True, string='Hotel Commission Base Factor')
    group_fees_percentage = fields.Float('Hotel Commission %', tracking=True)
    additional_fees1 = fields.Float('Group %', tracking=True)
    additional_group1_id = fields.Many2one('customer.fees', string='Group',
                                           tracking=True)
    additional_group1_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'),
         ('platform_fees', 'Platform Fees')], string='Group Base Factor',
        tracking=True)
    brand_id = fields.Many2one('customer.fees', tracking=True)
    brand_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    brand_fees = fields.Float(tracking=True)
    management_id = fields.Many2one('customer.fees', tracking=True)
    management_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')],
        tracking=True)
    management_fees = fields.Float(tracking=True)
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
