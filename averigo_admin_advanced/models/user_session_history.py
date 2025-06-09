# -*- coding: utf-8 -*-

import json
from _operator import itemgetter
from datetime import datetime, timedelta

from odoo import fields, models, api, _


class UserSessionHistory(models.Model):
    _name = "user.session.history"
    _rec_name = 'sequence'
    _description = "App User Session History"
    _order = 'create_date desc'
    sequence = fields.Char(
        string="Sequence")
    user_id = fields.Many2one(
        'res.app.users', string="User")
    operator_id = fields.Many2one(
        'res.company', string="Operator Name")
    location_id = fields.Many2one(
        'res.partner', string="Location Name")
    micro_market_id = fields.Many2one(
        'stock.warehouse',
        string="Micromarket Name")
    session_date = fields.Datetime(
        string="Login Date & Time")
    purchase_qty = fields.Integer(
        string="Purchase Quantity",
        compute="_compute_purchase_qty")
    purchase_value = fields.Float(
        string="Purchase Value",
        compute="_compute_purchase_value")
    product_list = fields.One2many(
        'session.product.list', 'session_id',
        string="Product Lists")
    move_id = fields.Many2one(
        'account.move')
    tax_amount = fields.Float(
        string="Tax Amount",
        compute="_compute_tax_amount")
    crv_tax = fields.Float(
        string="Container Deposit Amount", compute="_compute_crv_tax")
    payment_method = fields.Char(
        string="Payment Method")
    card_last = fields.Char(
        string="Card Last")
    total_trans_amount = fields.Float()
    total_crv_amount = fields.Float()
    total_sales_amount = fields.Float()
    unique_identifier = fields.Char()
    room_no = fields.Char()
    membership_number = fields.Char("Memership Number")
    host_transaction = fields.Char()
    process_status = fields.Char()
    cash_amount = fields.Float()
    scanned_upc = fields.Char(
        string='Scanned UPC')
    payroll_name = fields.Char()
    cc_fees = fields.Float()
    app_fees = fields.Float()
    stored_fund_fees = fields.Float()
    brand_fees = fields.Float()
    management_fees = fields.Float()
    platform_fees = fields.Float()
    fixed_platform = fields.Boolean()
    room_cc = fields.Float()
    cash_adj = fields.Float()
    additional_fees1 = fields.Float()
    additional_group1_id = fields.Many2one('customer.fees', tracking=True)
    additional_group1_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'),
         ('platform_fees', 'Platform Fees')], tracking=True)
    group_id = fields.Many2one('customer.fees')
    group_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')])
    group_fees_percentage = fields.Float()
    brand_id = fields.Many2one('customer.fees')
    brand_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')])
    # brand_fees_percentage = fields.Float(tracking=True)
    management_id = fields.Many2one('customer.fees')
    management_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')])
    # management_fees_percentage = fields.Float(tracking=True)
    purchasing_group_id = fields.Many2one('customer.fees')
    purchasing_group_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'),
         ('platform_fees', 'Platform Fees')])
    purchasing_group_fees_percentage = fields.Float()
    national_sales_team_id = fields.Many2one('customer.fees')
    national_sales_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')])
    national_sales_fees_percentage = fields.Float()
    local_sales_team_id = fields.Many2one('customer.fees')
    local_sales_base_factor = fields.Selection(
        [('margin', 'Margin'), ('net_sales', 'Net Sales'),
         ('gross_sales', 'Gross Sales'), ('platform_fees', 'Platform Fees')])
    local_sales_fees_percentage = fields.Float()




    @api.depends('tax_amount')
    def _compute_tax_amount(self):
        """Compute tax amount"""
        for rec in self:
            rec.tax_amount = sum(rec.product_list.mapped('tax_amount'))

    @api.depends('crv_tax')
    def _compute_crv_tax(self):
        """Compute Container Deposit Amount amount"""
        for rec in self:
            rec.crv_tax = sum(rec.product_list.mapped('crv_tax'))

    @api.depends('purchase_qty')
    def _compute_purchase_qty(self):
        """Compute total purchase qty"""
        for rec in self:
            rec.purchase_qty = sum(rec.product_list.mapped('qty'))

    @api.depends('product_list')
    def _compute_purchase_value(self):
        """Compute total purchase value"""
        for rec in self:
            rec.purchase_value = sum(rec.product_list.mapped('net_price'))

    def action_view_products(self):
        """ View product_details """
        return {
            'name': _('Session History'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'user.session.history',
            'res_id': self.id,
            'target': 'new',
        }

    def check_discount(self, product_id, check_mm_id):
        """ function for checking discount applicable or not """
        # get possible featured product records
        featured_ids = self.env['featured.products'].with_user(
            1).search([('product_id', '=', product_id),
                       ('micro_market_id', 'in', [check_mm_id]),
                       ('end_date', '>=', datetime.today().date())
                       ],
                      order="start_date asc")
        # check for valid featured products
        featured_available = []
        if featured_ids:
            for feature in featured_ids:
                time_str = '{0:02.0f}:{1:02.0f}'.format(
                    *divmod(feature.end_time * 60, 60))
                if feature.end_date and feature.end_date:
                    end_dt = datetime(feature.end_date.year,
                                      feature.end_date.month,
                                      feature.end_date.day,
                                      int(time_str.split(":")[
                                              0]) if feature.end_time else 23,
                                      int(time_str.split(":")[
                                              1]) if feature.end_time else 59)
                    if end_dt >= datetime.today():
                        featured_available.append(feature)
                elif feature.end_date and not feature.end_time:
                    end_dt = datetime(feature.end_date.year,
                                      feature.end_date.month,
                                      feature.end_date.day, 23, 59)
                    if end_dt >= datetime.today():
                        featured_available.append(feature)
                elif not feature.end_date and feature.end_time:
                    end_dt = datetime(datetime.today().year,
                                      datetime.today().month,
                                      datetime.today().day,
                                      int(time_str.split(":")[
                                              0]) if feature.end_time else 23,
                                      int(time_str.split(":")[
                                              1]) if feature.end_time else 59)
                    if end_dt >= datetime.today():
                        featured_available.append(feature)
        return "Y" if featured_available and featured_available[
            0].discount > 0.0 else "N"

    def get_top_product_details(self, base_url, mm_id):
        """ Get top sold product details for a specific Micromarket"""
        qry = """
                    select sp.product_id as p_id,sum(sp.qty) as qty
                    from user_session_history us
                    left join session_product_list sp
                    on sp.session_id = us.id
                    where us.micro_market_id = %s and sp.product_id is not NULL
                    and age( us.create_date, now() ) < '30 days'
                    group by p_id order by qty desc limit 10
                """ % mm_id
        self.env.cr.execute(qry)
        query_results = self.env.cr.dictfetchall()
        lst = []
        # prepare product list
        if query_results:
            for result in query_results:
                product = self.env['product.product'].with_user(1). \
                    browse(int(result['p_id']))
                mm_pool = self.env['stock.warehouse'].with_user(1). \
                    browse(int(mm_id))
                mm_product_id = mm_pool.market_product_ids.filtered(
                    lambda x: x.product_id.id == result['p_id'])
                tax_name = self.env['additional.tax'].sudo().search(
                    [('operator_id', '=', mm_pool.company_id.id)],
                    limit=1) if mm_pool.addl_tax else False
                if mm_product_id and mm_product_id.list_price != 0 and not mm_product_id.is_discontinued:

                    # Updated the function for Vendsys sales tax

                    if mm_pool.handled_externally and mm_product_id.tax_status == 'yes':
                        sale_tax = str(mm_product_id.vms_sales_tax)
                    elif mm_product_id.tax_status == 'yes':
                        sale_tax = str(mm_product_id.sales_tax)
                    else:
                        sale_tax = "0.00"

                    lst.append({
                        "CATEGORY_ID": str(product.categ_id.id) or '',
                        "ITEM_DESC_LONG": product.description or '',
                        "ORIGINAL_PRICE": str(format(mm_product_id.list_price, '.2f')),
                        "ITEM_IMAGE_URL": '%s/web/image_get?model=product.category&id=%d&field=category_image' % (
                            base_url, product.categ_id.id),
                        "ITEM_NO": mm_product_id.product_code or '',
                        "CRVTAX": str(
                            mm_product_id.container_deposit_tax.amount) if mm_product_id.container_deposit_tax else '0.00',
                        "SALESTAX": sale_tax,
                        "DISCOUNT_PRICE": str(format(mm_product_id.list_price, '.2f')),
                        "TAXABLE": "Y" if product.tax_status == 'yes' else "N",
                        "ITEM_DESC": product.name,
                        "STOCK": "Y" if mm_product_id.quantity >= 0 else "N",
                        "IsSpecial": "N",
                        "IsFeatured": "N",
                        "TOTAL_SOLD": str(result['qty']),
                        "BAR_CODE": str(
                            product.upc_ids.mapped('upc_code_id'))
                        [1:-1].replace(" ", '').replace("'", ''),
                        "ITEM_IMAGE": '%s/web/image_get?model=product.product&id=%d&field=image_1920' % (
                            base_url, product.id),
                        "DISCOUNT_APPLICABLE": self.check_discount(
                            int(result['p_id']), mm_id),
                        "CRV_ENABLE": "Y" if product.is_container_tax else "N",
                        "ITEM_PRICE": str(format(mm_product_id.list_price, '.2f')),
                        "PRODUCT_INFO": mm_product_id.info or "",
                        "OUTSIDE_MARKET_CATEGORY": "Y" if mm_product_id.categ_id.available_outside else "N",
                        "ADDL_TAX1_NAME": tax_name.additional_tax_label_1 if tax_name and mm_product_id.tax_rate_percentage_1 > 0 and mm_pool.show_tax_rate_1 and mm_product_id.enable_tax_rate_1 == 'yes' else "",
                        "ADDL_TAX1_VALUE": str(
                            mm_product_id.tax_rate_percentage_1) if tax_name and mm_product_id.tax_rate_percentage_1 > 0 and mm_pool.show_tax_rate_1 and mm_product_id.enable_tax_rate_1 == 'yes' else "",
                        "ADDL_TAX2_NAME": tax_name.additional_tax_label_2 if tax_name and mm_product_id.tax_rate_percentage_2 > 0 and mm_pool.show_tax_rate_2 and mm_product_id.enable_tax_rate_2 == 'yes' else "",
                        "ADDL_TAX2_VALUE": str(
                            mm_product_id.tax_rate_percentage_2) if tax_name and mm_product_id.tax_rate_percentage_2 > 0 and mm_pool.show_tax_rate_2 and mm_product_id.enable_tax_rate_2 == 'yes' else "",
                        "ADDL_TAX3_NAME": tax_name.additional_tax_label_3 if tax_name and mm_product_id.tax_rate_percentage_3 > 0 and mm_pool.show_tax_rate_3 and mm_product_id.enable_tax_rate_3 == 'yes' else "",
                        "ADDL_TAX3_VALUE": str(
                            mm_product_id.tax_rate_percentage_3) if tax_name and mm_product_id.tax_rate_percentage_3 > 0 and mm_pool.show_tax_rate_3 and mm_product_id.enable_tax_rate_3 == 'yes' else "",

                    })
        return lst

    @api.model
    def create(self, vals_list):
        """Function for generating sequence"""
        res = super().create(vals_list)
        ref = self.env.ref('averigo_admin_advanced.app_user_session_sequence')
        sequence = ref.with_user(1).next_by_code("user.session.history") or _('New')
        res.sequence = sequence
        return res


class SessionProductList(models.Model):
    _name = 'session.product.list'
    _description = 'Session Products List'

    session_id = fields.Many2one(
        'user.session.history', string="Session ID")
    product_id = fields.Many2one(
        'product.product', string="Product")
    qty = fields.Integer(
        string="Quantity")
    product_uom_id = fields.Many2one(
        'uom.uom',string='Unit of Measure', readonly=True)
    price = fields.Float(
        string="Price")
    net_price = fields.Float(
        string="Net")
    tax_amount = fields.Float(
        string="Tax Amount")
    crv_tax = fields.Float(
        string="Container Deposit Amount")
    featured = fields.Char()
    list_price = fields.Float(
        string="List Price")
    special = fields.Char()
    user_type = fields.Char()
