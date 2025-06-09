from odoo import fields, models, api, _


class TransactionFeesUpdate(models.TransientModel):
    _name = 'transaction.fees.update'
    _description = 'Wizard for fees updated in Transactions'

    micro_market_ids = fields.Many2many('stock.warehouse')
    mm_dom_ids = fields.Many2many('stock.warehouse', compute='_compute_mm_ids')
    company_ids = fields.Many2many('res.company')
    start_date = fields.Date()
    end_date = fields.Date()

    @api.depends('company_ids')
    def _compute_mm_ids(self):
        """Compute available micro market IDs excluding those already in use."""
        for record in self:
            record.mm_dom_ids = False
            if record.company_ids:
                domain = [
                    ('company_id', 'in', record.company_ids.ids),
                    ('location_type', '=', 'micro_market')]
            else:
                domain = [
                    ('company_id.active', '=', True),
                    ('location_type', '=', 'micro_market')]
            all_mm_ids = self.env['stock.warehouse'].sudo().search(domain)
            record.mm_dom_ids = all_mm_ids

    def update(self):
        query = """
            UPDATE user_session_history
            SET 
                cc_fees = sw.cc_fees,
                app_fees = sw.app_fees,
                stored_fund_fees = sw.stored_fund_fees,
                brand_fees = sw.brand_fees,
                management_fees = sw.management_fees,
                platform_fees = sw.platform_fees,
                fixed_platform = CASE sw.platform_fees_type
                                    WHEN 'percentage' THEN FALSE
                                    WHEN 'fixed' THEN TRUE
                                 END,
                room_cc = sw.room_cc,
                cash_adj = sw.cash_adj,
                additional_group1_id = sw.additional_group1_id,
                additional_group1_base_factor = sw.additional_group1_base_factor,
                additional_fees1 = sw.additional_fees1,
                group_id = sw.group_id,
                group_base_factor = sw.group_base_factor,
                group_fees_percentage = sw.group_fees_percentage,
                brand_id = sw.brand_id,
                brand_base_factor = sw.brand_base_factor,
                management_id = sw.management_id,
                management_base_factor = sw.management_base_factor,
                purchasing_group_id = sw.purchasing_group_id,
                purchasing_group_base_factor = sw.purchasing_group_base_factor,
                purchasing_group_fees_percentage = sw.purchasing_group_fees_percentage,
                national_sales_team_id = sw.national_sales_team_id,
                national_sales_base_factor = sw.national_sales_base_factor,
                national_sales_fees_percentage = sw.national_sales_fees_percentage,
                local_sales_team_id = sw.local_sales_team_id,
                local_sales_base_factor = sw.local_sales_base_factor,
                local_sales_fees_percentage = sw.local_sales_fees_percentage
            FROM stock_warehouse sw
            WHERE sw.id = user_session_history.micro_market_id
              AND user_session_history.create_date >= '%s'::DATE
        """ % self.start_date
        if self.end_date:
            query += (
                        " AND (user_session_history.session_date::DATE <= '%s'::DATE)" % self.end_date)
        if self.micro_market_ids:
            if len(self.micro_market_ids.ids) > 1:
                query += (
                            " AND (user_session_history.micro_market_id in %s)" % str(
                        tuple(self.micro_market_ids.ids)))
            else:
                query += (" AND (user_session_history.micro_market_id = %s)" %
                          tuple(self.micro_market_ids.ids)[0])
        else:
            if self.operator_ids and len(self.operator_ids) > 1:
                query += (" AND (user_session_history.operator_id in %s)" % str(
                    tuple(self.operator_ids.ids)))
            elif self.operator_ids:
                query += (" AND (user_session_history.operator_id = %s)" %
                          tuple(self.operator_ids.ids)[0])
        self.env.cr.execute(query)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Transaction Fees Updated',
                'message': 'Fees are updated in the transactions',
                'sticky': False,
            }
        }
