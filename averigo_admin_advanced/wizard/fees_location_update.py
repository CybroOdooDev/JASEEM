# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timezone
from odoo.exceptions import UserError, ValidationError


class FeesLocationUpdate(models.TransientModel):
    _name = 'fees.location.update'

    micro_market_ids = fields.Many2many('stock.warehouse')
    fees_template_id = fields.Many2one('fees.distribution')
    select_micro_market = fields.Selection(
        [('all', 'All'), ('select', 'Select Micromarkets')], default='all')
    list_micro_market_id = fields.Many2many('stock.warehouse',
                                            'fees_stock_warehouse_rel')

    def process(self):
        micro_market_ids = self.micro_market_ids if self.select_micro_market == 'all' else self.list_micro_market_id
        for micro_market_id in micro_market_ids:
            micro_market_id.fees_template_id = self.fees_template_id.id
            micro_market_id.cc_fees = self.fees_template_id.cc_fees
            micro_market_id.app_fees = self.fees_template_id.app_fees
            micro_market_id.stored_fund_fees = self.fees_template_id.stored_fund_fees
            micro_market_id.platform_fees = self.fees_template_id.platform_fees
            micro_market_id.room_cc = self.fees_template_id.room_cc
            micro_market_id.cash_adj = self.fees_template_id.cash_adj
            micro_market_id.group_id = self.fees_template_id.group_id
            micro_market_id.group_base_factor = self.fees_template_id.group_base_factor
            micro_market_id.group_fees_percentage = self.fees_template_id.group_fees_percentage
            micro_market_id.additional_fees1 = self.fees_template_id.additional_group1_fees_percentage
            micro_market_id.additional_group1_id = self.fees_template_id.additional_group1_id
            micro_market_id.additional_group1_base_factor = self.fees_template_id.additional_group1_base_factor
            micro_market_id.brand_id = self.fees_template_id.brand_id
            micro_market_id.brand_base_factor = self.fees_template_id.brand_base_factor
            micro_market_id.brand_fees = self.fees_template_id.brand_fees_percentage
            micro_market_id.management_id = self.fees_template_id.management_id
            micro_market_id.management_base_factor = self.fees_template_id.management_base_factor
            micro_market_id.management_fees = self.fees_template_id.management_fees_percentage
            micro_market_id.purchasing_group_id = self.fees_template_id.purchasing_group_id
            micro_market_id.purchasing_group_base_factor = self.fees_template_id.purchasing_group_base_factor
            micro_market_id.purchasing_group_fees_percentage = self.fees_template_id.purchasing_group_fees_percentage
            micro_market_id.national_sales_team_id = self.fees_template_id.national_sales_team_id
            micro_market_id.national_sales_base_factor = self.fees_template_id.national_sales_base_factor
            micro_market_id.national_sales_fees_percentage = self.fees_template_id.national_sales_fees_percentage
            micro_market_id.local_sales_team_id = self.fees_template_id.local_sales_team_id
            micro_market_id.local_sales_base_factor = self.fees_template_id.local_sales_base_factor
            micro_market_id.local_sales_fees_percentage = self.fees_template_id.local_sales_fees_percentage
            if self.fees_template_id.platform_fees_per_day:
                micro_market_id.platform_fees_per_day = self.fees_template_id.local_sales_fees_percentage


