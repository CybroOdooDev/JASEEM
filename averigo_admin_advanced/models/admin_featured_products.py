# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from pytz import timezone

class AdminFeaturedProducts(models.Model):
    _name = "admin.featured.products"
    _description = 'Admin Featured Products'

    image = fields.Binary(
        string='Image', copy=0, attachment=True)
    company_ids = fields.Many2many(
        'res.company', 'Operator', required=True, index=True,
        default=lambda self: self.env.company)
    company_filter_ids = fields.Many2many(
        'res.company', 'company_filter_ids_rel',
        store=True, compute='compute_company_filter_ids')
    location_ids = fields.Many2many('res.partner', 'admin_featured_products_res_partner_rel',
        string='Customer',domain="[('operator_id', 'in', company_ids), ('is_customer', '=', True)]")
    location_filter_ids = fields.Many2many(
        'res.partner', compute='_compute_micro_market_id')
    micro_market_ids = fields.Many2many('stock.warehouse',
                                       'featured_product_stock_warehouse_rel',
                                       'product_id',
                                       'warehouse_id',
                                       domain=[('location_type', '=',
                                                'micro_market')],
                                        )
    market_ids = fields.Many2many(
        'stock.warehouse',compute='_compute_micro_market_id')
    product_ids = fields.Many2many(
        'product.product',
        string="Product", copy=False)
    product_dom_ids = fields.Many2many(
        'product.product', compute='_compute_micro_market_id')
    discount = fields.Float(
        string="Discount %", copy=False, default=0)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="Stop Date")
    start_time = fields.Float(string="Start Time")
    end_time = fields.Float(string="Stop Time")
    start_time_display = fields.Float(
        string="Start Time")
    end_time_display = fields.Float(
        string="Stop Time")
    t_start_seconds = fields.Integer(
        string="Start Seconds")
    t_start_period = fields.Selection(
        [('am', 'AM'), ('pm', 'PM')], default='am')
    t_end_seconds = fields.Integer(
        string="End Seconds")
    t_end_period = fields.Selection(
        [('am', 'AM'), ('pm', 'PM')], default='am')
    time_format = fields.Selection(
        [('hm', 'HH:MM'), ('hms', 'HH:MM:SS'), ('imp', 'HH:MM AM/PM'),
         ('ims', 'HH:MM:SS AM/PM')],
        string="Time Format", related="company_id.time_format_selection")

    banner_type = fields.Selection([
        ('url', 'Video URL'),
        ('image', 'Image'),
    ], default='image', required=True, )
    product_associated = fields.Many2one('product.product',
                                         string="Image to Associate")
    url = fields.Char(
        string='URL')
    banner_text = fields.Char()
    company_id = fields.Many2one(
        'res.company', string="Company", index=True,
        default=lambda self: self.env.company)
    send_notification = fields.Boolean(
        default=False)
    update_date = fields.Date(
        string="Update Date")
    mm_ids = fields.Many2many(
        'stock.warehouse', 'admin_featured_products_stock_warehouse_rel2',
        'product_id2', 'warehouse_id2', copy=False)

    @api.onchange('location_ids')
    def _onchange_location_ids(self):
        markets = self.env['stock.warehouse'].search([
            ('company_id', 'in', self.company_ids.ids),('partner_id','in',self.location_ids.ids)
        ])

        if not self.location_ids:
            self.micro_market_ids=[(5, 0, 0)]
            self.product_ids=[(5, 0, 0)]
        else:
            market_ids = self.micro_market_ids.ids
            total_markets = markets.mapped('id')

            ids_to_remove = list(set(market_ids) - set(total_markets))
            if ids_to_remove:
                self.micro_market_ids = [(3, id, 0) for id in ids_to_remove]
                self.product_ids = [(5, 0, 0)]

    @api.depends('company_ids')
    def compute_company_filter_ids(self):
        for rec in self:
            all_companies = rec.company_ids
            rec.company_filter_ids = all_companies
            all_customers = self.env['res.partner'].search([
                ('operator_id', 'in', self.company_ids.ids),
                ('is_customer', '=', True)
            ])
            rec.location_filter_ids = all_customers
        if not self.company_ids:
            self.location_ids = [(5, 0, 0)]

    @api.depends('location_ids','micro_market_ids','product_ids')
    def _compute_micro_market_id(self):
        all_customers = self.env['res.partner'].search([
            ('operator_id', 'in', self.company_ids.ids),
            ('is_customer', '=', True),
            ('is_frontend_boolean', '=', False),
            ('parent_id', '=', False),
            ('type', '=', 'contact')
        ])

        for rec in self:
            selected_market = rec.micro_market_ids
            selected_pdts = rec.product_ids
            if rec.location_ids:
                selected_partners = self.env['res.partner'].browse(all_customers.mapped('id'))
                new_partner = self.env['res.partner'].browse(rec.location_ids.mapped('id'))

                filtered_partners = list(set(selected_partners.ids) - set(new_partner.ids))
                rec.location_filter_ids = filtered_partners

                market_id = rec.env['stock.warehouse'].search([('location_type', '=', 'micro_market'),('partner_id', 'in', rec.location_ids.ids)])
                rec.market_ids = market_id

                filtered_markets = list(set(rec.market_ids.ids) - set(selected_market.ids))
                if filtered_markets:
                    rec.market_ids = filtered_markets
                else:
                    rec.market_ids = False
                if rec.micro_market_ids:
                    micro_market_product_ids = rec.micro_market_ids.market_product_ids.mapped(
                        'product_id')
                    rec.product_dom_ids = micro_market_product_ids.ids

                    filtered_pdt = list(set(rec.product_dom_ids.ids) - set(selected_pdts.ids))
                    if filtered_pdt:
                        rec.product_dom_ids = filtered_pdt
                    else:
                        rec.product_dom_ids = False
                else:
                    # Get products from all micro markets
                    product_ids = self.env['product.product'].search([])
                    rec.product_dom_ids = product_ids.ids
            else:
                rec.location_filter_ids = all_customers
                market_id = self.env['stock.warehouse'].search(
                    [('location_type', '=', 'micro_market'),
                     ('company_id', '=', self.env.user.company_id.id)])
                rec.market_ids = market_id
                rec.product_dom_ids = self.env['product.product'].search([])

    def _get_24_time(self, time, period, sec):
        """Converts the given time to 24-hour format."""
        if time:
            decimal = str(time).split(".")[1]
            time = '{0:02.0f}:{1:02.0f}'.format(*divmod(time * 60, 60))
            period = 'PM' if period == 'pm' else 'AM'
            time_str = time + ":" + str("{:02d}".format(
                sec)) + ' ' + str(period)
            time_24 = self.convert24(time_str)
            time_array = time_24.split(":")
            float_time = float(".".join([time_array[0], decimal]))
            return float_time
        else:
            return False

    @api.onchange('t_start_seconds', 't_start_period', 't_end_seconds',
                  't_end_period', 'start_time_display', 'end_time_display')
    def change_time(self):
        """Updates the start and end times based on the selected time format."""
        self.check_time_format()
        if self.time_format in ['ims', 'imp']:
            if self.start_time_display:
                self.start_time = self._get_24_time(self.start_time_display,
                                                    self.t_start_period,
                                                    self.t_start_seconds)
            if self.end_time_display:
                self.end_time = self._get_24_time(self.end_time_display,
                                                  self.t_end_period,
                                                  self.t_end_seconds)
        else:
            self.start_time = self.start_time_display
            self.end_time = self.end_time_display

    def check_time_format(self):
        """Validates the time format."""
        if self.t_start_period and self.time_format in ['imp', 'ims']:
            if self.start_time_display > 12:
                self.start_time_display = False
                raise UserError(_("Invalid time provided in Start Time, "
                                  "please check and try again!"))
            if self.end_time_display > 12:
                self.end_time_display = False
                raise UserError(_("Invalid time provided in End Time, "
                                  "please check and try again!"))
        if self.time_format in ['hm', 'hms']:
            if self.start_time_display > 24:
                self.start_time_display = False
                raise UserError(_("Invalid time provided in Start Time, "
                                  "please check and try again!"))
            if self.end_time_display > 24:
                self.end_time_display = False
                raise UserError(_("Invalid time provided in End Time, "
                                  "please check and try again!"))
    def convert24(self, str1):
        """Converts a 12-hour time format to 24-hour format."""
        # Checking if last two elements of time
        # is AM and first two elements are 12
        if str1[-2:] == "AM" and str1[:2] == "12":
            return "00" + str1[2:-2]
            # remove the AM
        elif str1[-2:] == "AM":
            return str1[:-2]
            # Checking if last two elements of time
        # is PM and first two elements are 12
        elif str1[-2:] == "PM" and str1[:2] == "12":
            return str1[:-2]
        else:
            # add 12 to hours and remove PM
            return str(int(str1[:2]) + 12) + str1[2:8]

    @api.model
    def create(self, vals_list):
        """Creates a new record with additional validations."""
        utc = timezone("US/Pacific")
        date_format = '%Y-%m-%d'
        date = datetime.now(tz=utc)
        date = date.astimezone(timezone('US/Pacific'))
        day = date.strftime(date_format)
        vals_list['update_date'] = day


        if 'end_date' in vals_list and 'start_date' in vals_list \
                and vals_list['end_date'] < vals_list['start_date']:
            raise UserError(_("Inconsistent start and end dates! \n"
                              "Stop date should be above the start date. "
                              "Please check the date fields and try again."))
        if 'start_time' in vals_list and 'end_time' in vals_list \
                and vals_list['end_time'] < vals_list['start_time']:
            raise UserError(_("Inconsistent start and end time! \n"
                              "Stop time should be above the start time. "
                              "Please check the time fields and try again."))
        if vals_list['start_time'] < 0 or vals_list['end_time'] < 0 or vals_list['start_time'] > 24.0 or vals_list[
            'end_time'] > 24.0:
            raise UserError(_("Inconsistent start and end time! \n"
                              "Time should be 0 to 24.0! "
                              "Please check the time fields and try again."))
        if vals_list['start_time'] == vals_list['end_time']:
            raise UserError(_("Start and End Time Can not be the same."))
        if 'micro_market_ids' in vals_list:
            vals_list['mm_ids'] = vals_list['micro_market_ids']
        elif 'location_ids' in vals_list:
            location = vals_list['location_ids'][0][2]
            location = self.env['stock.warehouse'].search([('partner_id', 'in', location)]).ids
            vals_list['mm_ids'] = [[6, False, location]]
        else:
            company_ids = self.env['stock.warehouse'].search([('company_id', '=', self.company_ids.ids)]).ids
            vals_list['mm_ids'] = [[6, False, company_ids]]
        res = super(AdminFeaturedProducts, self).create(vals_list)
        return res

