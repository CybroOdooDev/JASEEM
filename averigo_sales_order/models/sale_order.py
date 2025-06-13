# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CustomerSaleOrder(models.Model):
    """ inheriting sale order model"""
    _inherit = 'sale.order'
    _description = "Quotation/Order"

    def _get_country(self):
        """ Get default country as United States"""
        country = self.env.ref('base.us').id
        return country

    def _set_current_date(self):
        """ get current date as promise date"""
        return fields.Date.today()

    @api.model
    def _default_warehouse_id(self):
        """Set up the warehouse_id as default warehouse id setup in operator"""
        warehouse_id = self.env.company.default_warehouse_id
        if not warehouse_id:
            warehouse_id = self.env['stock.warehouse'].sudo().search(
                [('location_type', '=', 'view'),
                 ('is_parts_warehouse', '=', False)], limit=1)
        return warehouse_id

    averigo_sale_order = fields.Boolean(
        default=True)
    portal_view = fields.Boolean(
        default=False)
    kam = fields.Many2one(
        'hr.employee', string='Accounts Manager')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        change_default=True,
        index=True, tracking=1, domain="[('type', 'in', ['contact', 'portal']),"
                                       "('is_customer', '=', True)]")
    commitment_date = fields.Datetime(
        'Delivery Date', copy=False, readonly=True,
        help="This is the delivery date promised to the customer. "
             "If set, the delivery order will be scheduled "
             "based on this date rather than product lead times.")
    promise_date = fields.Date(
        string="Promise Date", copy=False, default=_set_current_date)
    route_id = fields.Many2one(
        'route.route', string='Route')
    delivery_date = fields.Date(
        string='Delivery Date')
    portal_delivery_date = fields.Datetime(
        string='Delivery Date')
    note = fields.Text()
    message = fields.Text()
    notes = fields.Text()
    contact = fields.Char(
        'Contact Name')
    po_no = fields.Char(
        'PO #')
    sale_po_date = fields.Date(
        'PO Date')
    customer_user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user)
    sell_all_item = fields.Boolean(
        string="Sell All Products")
    cus_product_associate = fields.Boolean(
        store=True, default=True, compute='_compute_product_count')
    cus_product_assoc_ids = fields.Many2many(
        'product.product', 'cus_product_assoc_rel',
        string='Customer Products')
    cus_product_filter_ids = fields.Many2many(
        'product.product', compute='_compute_cus_product_filter_ids')
    total_qty = fields.Integer(
        'Total Quantity', compute='_compute_total_qty')
    message_len = fields.Integer(
        'Message Length', compute='_compute_message_len')
    add_button = fields.Boolean(
        'Add')
    total_weight = fields.Float()
    desc_check = fields.Boolean(
        compute='_compute_description')
    change_address_wizard = fields.Boolean(
        string='Change address', default=True)
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Billing Address', store=True,
        domain="[('id', 'in', partner_invoice_ids)]")
    partner_invoice_ids = fields.Many2many(
        'res.partner', relation='partner_invoice',
        compute='_compute_partner_invoice_ids')
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Shipping Address', store=True,
        domain="[('id', 'in', partner_shipping_ids)]")
    partner_shipping_ids = fields.Many2many(
        'res.partner', relation='partner_shipping',
        compute='_compute_partner_shipping_ids')
    country_id = fields.Many2one(
        'res.country', string="Ship to Country",
        default=_get_country)
    inv_street = fields.Char(
        'Bill to Street')
    inv_street2 = fields.Char(
        'Bill to Street2')
    inv_zip = fields.Char(
        'Bill to Zip', size=5)
    inv_city = fields.Char(
        'Bill to City')
    inv_county = fields.Char(
        'Bill to County')
    inv_state_id = fields.Many2one(
        'res.country.state', string="Bill to State",
        domain="[('country_id', '=?', country_id)]")
    shp_street = fields.Char(
        'Ship to Street')
    shp_street2 = fields.Char(
        'Ship to Street2')
    shp_zip = fields.Char(
        'Ship to Zip', size=5)
    shp_city = fields.Char(
        'Ship to City')
    shp_county = fields.Char(
        'Ship to County')
    shp_state_id = fields.Many2one(
        'res.country.state', string="Ship to State",
        ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    shipping_handling = fields.Float()
    insurance = fields.Float()
    tax_amount_view = fields.Float()
    tax_calc = fields.Float()
    tax_rate_is = fields.Boolean(default=False)
    total_container_deposit = fields.Float(
        compute='_compute_total_discount')
    total_discount = fields.Float(
        compute='_compute_total_discount')
    total_discount_view = fields.Float()
    container_deposit_view = fields.Float()
    fob = fields.Selection(
        [('origin', 'Origin'), ('dest', 'Destination')],
        default='origin', string='FOB')
    ship_via = fields.Many2one(
        'ship.via', string='Ship Via')
    hold_reason = fields.Many2one(
        'hold.reason')
    closed_reason = fields.Many2one(
        'closed.reason')
    drop_location_id = fields.Many2one(
        'drop.location', string='Drop Off Location')
    drop_ship = fields.Boolean(
        'Drop shipping')
    drop_partner_id = fields.Many2one(
        'res.partner', string='Vendor')
    route_truck_driver = fields.Char()
    print = fields.Boolean(
        string='To Be Printed')
    sale_order_state = fields.Selection([
        ('draft', 'Open'),
        ('sent', 'Order Sent'),
        ('sale', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft',
        compute='_compute_sale_order_state')
    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Location',
        domain="[('location_type', '=', 'view'), "
               "('is_parts_warehouse', '=', False)]", required=True,
        default=_default_warehouse_id, check_company=True)
    show_cp_code = fields.Boolean(
        compute="_compute_show_cp_code")
    total_product_quantity = fields.Integer(
        string='Total Quantity', readonly=True)
    contain_service_product = fields.Boolean(
        compute='_compute_contain_service_product',
        help="Become true when there is any service product in orderline")
    associated_product = fields.Boolean(
        string='Add Associated Products')
    is_closed = fields.Boolean(
        'is closed', invisible=True)
    tax_type = fields.Selection(
        [('sales', 'Sales Tax'), ('scheduled', 'Scheduled Tax')],
        'Tax Type', default='sales')
    schedule_tax_id = fields.Many2one(
        'schedule.tax')
    portal_order_view = fields.Boolean(
        default=False)
    service_product_ids = fields.Many2many(
        'product.product', 'sale_order_id',
        string='Service Products', domain="[('product_type', '=', 'service')]",
        check_company=True)
    is_add_service_product_button = fields.Boolean()
    is_customer_credit = fields.Boolean()

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ to set po_no"""
        if self.partner_id:
            self.po_no = self.partner_id.po_no
        else:
            self.po_no = False

    @api.onchange('commitment_date')
    def _onchange_commitment_date(self):
        """ Warning if the commitment dates is sooner than the expected date """
        if self.commitment_date and self.expected_date and self.commitment_date < self.expected_date:
            return {
                'warning': {
                    'title': _('Requested date is too soon.'),
                    'message': _(
                        "The delivery date is sooner than the expected date."
                        " You may be unable to honor the delivery date.")
                }
            }

    @api.onchange("promise_date")
    def _onchange_promise_date(self):
        """ to give warning based on order and promise date"""
        self.commitment_date = self.promise_date
        if self.promise_date:
            utc_promise_date = self.promise_date.isoformat()
            utc_date_order = self.date_order.date().isoformat()
            if utc_promise_date < utc_date_order:
                raise UserError(
                    _("promise date should be greater than the order " "date"))

    @api.depends('order_line')
    def _compute_contain_service_product(self):
        """ to check whether service product is added"""
        for rec in self:
            service_products = rec.order_line.mapped('product_id').filtered(
                lambda s: s.product_type == 'service')
            rec.write({'contain_service_product': False})
            if service_products:
                rec.write({'contain_service_product': True})

    @api.onchange('is_add_service_product_button')
    def _onchange_add_service_product_button(self):
        """ boolean to add service products"""
        self.add_service_product()

    def add_service_product(self):
        """ fun to add service products"""
        for product in self.service_product_ids:
            if self.partner_id.price_category == 'list_price_1':
                price = product.list_price_1
            elif self.partner_id.price_category == 'list_price_2':
                price = product.list_price_2
            elif self.partner_id.price_category == 'list_price_3':
                price = product.list_price_3
            else:
                price = product.list_price_1
            self.write({
                'order_line': [(0, 0, {
                    'name': product.product_tmpl_id.name,
                    'product_code': product.product_tmpl_id.default_code,
                    'unit_price': price,
                    'product_id': product._origin.id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': 0,
                    'tax_status': product.tax_status

                })]
            })
            self.service_product_ids = None

    @api.depends('state')
    def _compute_sale_order_state(self):
        """ to compute sale order state"""
        for rec in self:
            rec.sale_order_state = rec.state

    @api.depends('name')
    def _compute_show_cp_code(self):
        """ fun to enable and disable cp code"""
        sales_default = self.env['sales.default'].sudo().search(
            [('company_id', '=', self.env.company.id)])
        for rec in self:
            rec.show_cp_code = sales_default.enable_cp_code

    @api.depends('partner_id')
    def _compute_product_count(self):
        """Function to compute the number of product in customer Products"""
        for rec in self:
            partner_id = rec.partner_id.parent_id if rec.partner_id.parent_id else rec.partner_id
            product_ids = partner_id.sudo().mapped('customer_product_ids')
            if partner_id and len(product_ids) > 0:
                rec.cus_product_associate = True
            elif partner_id:
                rec.cus_product_associate = False

    @api.depends('partner_id', 'sell_all_item', 'order_line.product_id')
    def _compute_cus_product_filter_ids(self):
        """ compute products based on partner, sell all item"""
        product_ids = self.env['product.product'].sudo().search(
            [('product_type', '=', 'product'), ('operator_id', '=', self.company_id.id)])
        for rec in self:
            rec.cus_product_filter_ids = None
            if rec.partner_id:
                if rec.sell_all_item:
                    rec.cus_product_filter_ids += product_ids
                else:
                    if not rec.partner_id.buy_all_item:
                        products = rec.partner_id.customer_product_ids.sudo().mapped(
                            'product_id') - rec.order_line.mapped('product_id')
                        rec.cus_product_filter_ids += products
                    elif rec.partner_id.buy_all_item:
                        rec.cus_product_filter_ids += product_ids

    @api.onchange('sell_all_item')
    def _onchange_sell_all_item(self):
        """ sell all items based on boolean field sell all item"""
        if self.sell_all_item and not self.partner_id:
            raise UserError(_("Please select a customer to sell all item"))

    @api.onchange('associated_product')
    def _onchange_associated_product(self):
        """ to provide warning based on associated products """
        if self.associated_product and not self.partner_id:
            raise UserError(
                _("Please select a customer to add associated products"))
        elif self.associated_product:
            self.cus_product_assoc_ids = self.partner_id.customer_product_ids.sudo().mapped(
                'product_id') - self.order_line.product_id
            for rec in self:
                rec.add_products()
            associated_order_lines = self.order_line.filtered(
                lambda
                    s: s.product_id.id in self.partner_id.customer_product_ids.sudo().mapped(
                    'product_id').ids)
            associated_order_lines.write({'asso_products': True})
        else:
            associated_order_lines = self.order_line.filtered(
                lambda
                    s: s.product_id.id in self.partner_id.customer_product_ids.sudo().mapped(
                    'product_id').ids)
            self.order_line = self.order_line - associated_order_lines

    @api.onchange('add_button')
    def _onchange_add_button(self):
        """ to call function when add button changes"""
        self.add_products()

    def add_products(self):
        """ functon to add products to orderline"""
        if self.cus_product_assoc_ids:
            product_list = []
            customer_products = self.partner_id.sudo().customer_product_ids
            customer_products_ids = customer_products.sudo().mapped(
                'product_id')
            cus_prod_list = []
            cus_prod_name = []
            for product in self.cus_product_assoc_ids:
                product = product._origin
                customer_product = customer_products.filtered(
                    lambda s: s.product_id.id == product.id)
                for item in customer_product:
                    if product in customer_products_ids:
                        order_lines = (0, 0, {
                            'product_id': product.id,
                            'name': item.name,
                            'cp_code': item.cp_code,
                            'desc': product.description_sale,
                            'bin_location_id': product.primary_location.id if product.primary_location.id else self.warehouse_id.lot_stock_id.id,
                            'product_uom': item.uom_id.id,
                            'product_uom_qty': 0,
                            'unit_price': item.list_price,
                            'tax_status': item.tax_status,
                        })
                        product_list.append(order_lines)
                if product not in customer_products_ids:
                    cus_prod_list.append(product.id)
                    cus_prod_name.append(product.name)
                    name = ', '.join(cus_prod_name).replace('False,', '')
                    order_lines = {
                        'product_id': product.id,
                        'name': product.name,
                        'desc': product.description_sale,
                        'bin_location_id': product.primary_location.id if product.primary_location.id else self.warehouse_id.lot_stock_id.id,
                        'product_uom': product.uom_id.id,
                        'unit_price': product.list_price_1,
                        'tax_status': product.tax_status,
                    }
                    if self.partner_id.price_category == 'list_price_1':
                        order_lines.update({
                            'unit_price': product.list_price_1,
                        })
                    elif self.partner_id.price_category == 'list_price_2':
                        order_lines.update({
                            'unit_price': product.list_price_2,
                        })
                    elif self.partner_id.price_category == 'list_price_3':
                        order_lines.update({
                            'unit_price': product.list_price_3,
                        })
                    elif not self.partner_id.price_category:
                        order_lines.update({
                            'unit_price': product.list_price_1,
                        })
                    vals = (0, 0, order_lines)
                    product_list.append(vals)
            self.order_line = [(2, 0, 0)] + product_list
            self.cus_product_assoc_ids = None
            product_confirmation_wiz = self.env.ref(
                'averigo_sales_order.view_product_confirmation_wizard').id
            if cus_prod_list:
                products_m2m = self.env['product.product'].sudo().search(
                    [('id', 'in', cus_prod_list)]).ids
                ctx = dict(self.env.context or {})
                ctx.update({
                    'default_name': name,
                    'default_partner_id': self.partner_id.id,
                    'default_product_ids': products_m2m,
                })
                return {
                    'name': _('Product Confirmation'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'product.confirmation',
                    'view_id': product_confirmation_wiz,
                    'context': ctx,
                    'target': 'new',
                }

    @api.depends('user_id', 'company_id')
    def _compute_warehouse_id(self):
        """ overrides the addon function to set warehouse"""
        for order in self:
            default_warehouse_id = self.env['ir.default'].with_company(
                order.company_id.id)._get_model_defaults('sale.order').get(
                'warehouse_id')
            if order.state in ['draft', 'sent'] or not order.ids:
                # Should expect empty
                if default_warehouse_id is not None:
                    order.warehouse_id = default_warehouse_id
                elif order.averigo_sale_order:
                    order.warehouse_id = order.env.company.default_warehouse_id
                else:
                    order.warehouse_id = order.user_id.with_company(
                        order.company_id.id)._get_default_warehouse_id()

    @api.depends('warehouse_id')
    def _compute_description(self):
        company_id = self.env.context.get('company_id') or self.env.company.id
        picking_type = self.env['stock.picking.type'].sudo().search(
            [('code', '=', 'outgoing'),
             ('warehouse_id', '=', self.warehouse_id.id)], limit=1)
        if not picking_type.show_operations:
            picking_type.write({
                'show_operations': True
            })
        if not picking_type:
            picking_type = self.env['stock.picking.type'].sudo().search(
                [('code', '=', 'outgoing'), ('warehouse_id', '=', False)],
                limit=1)
            if not picking_type.show_operations:
                picking_type.write({
                    'show_operations': True
                })
        default = self.env['sales.default'].sudo().search(
            [('desc', '!=', False),
             ('company_id', '=',
              company_id)])
        for rec in self:
            rec.desc_check = False
            if default:
                rec.desc_check = True

    @api.depends('message')
    def _compute_message_len(self):
        """ to compute messages length"""
        for rec in self:
            rec.message_len = len(rec.message) if rec.message else 0

    @api.depends('partner_id')
    def _compute_partner_shipping_ids(self):
        """Compute invoice addresses for partner and their parent"""
        for rec in self:
            if rec.partner_id:
                partner = self.env['res.partner'].sudo().search([
                    ('id', 'in', rec.partner_id.child_ids.ids),
                    ('type', '=', 'delivery')
                ])
                partner_parent = self.env['res.partner']
                if rec.partner_id.parent_id:
                    partner_parent = self.env['res.partner'].sudo().search([
                        ('id', 'in', rec.partner_id.parent_id.child_ids.ids),
                        ('type', '=', 'delivery')
                    ])
                rec.partner_shipping_ids = partner or partner_parent
            else:
                rec.partner_shipping_ids = self.env['res.partner']

    @api.depends('partner_id')
    def _compute_partner_invoice_ids(self):
        """Compute invoice addresses for partner and their parent"""
        for rec in self:
            if rec.partner_id:
                partner = self.env['res.partner'].sudo().search([
                    ('id', 'in', rec.partner_id.child_ids.ids),
                    ('type', '=', 'invoice')
                ])
                partner_parent = self.env['res.partner']
                if rec.partner_id.parent_id:
                    partner_parent = self.env['res.partner'].sudo().search([
                        ('id', 'in', rec.partner_id.parent_id.child_ids.ids),
                        ('type', '=', 'invoice')
                    ])
                rec.partner_invoice_ids = partner or partner_parent
            else:
                rec.partner_invoice_ids = self.env['res.partner']

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        if self.partner_shipping_id:
            if self.partner_shipping_id.tax_calc > 0:
                self.write({
                    'shp_street': self.partner_shipping_id.street,
                    'shp_street2': self.partner_shipping_id.street2,
                    'shp_zip': self.partner_shipping_id.zip,
                    'shp_city': self.partner_shipping_id.city,
                    'shp_county': self.partner_shipping_id.county,
                    'shp_state_id': self.partner_shipping_id.state_id.id,
                    'tax_calc': self.partner_shipping_id.tax_calc,
                    'tax_rate_is': False
                })
            else:
                self.write({
                    'shp_street': self.partner_shipping_id.street,
                    'shp_street2': self.partner_shipping_id.street2,
                    'shp_zip': self.partner_shipping_id.zip,
                    'shp_city': self.partner_shipping_id.city,
                    'shp_county': self.partner_shipping_id.county,
                    'shp_state_id': self.partner_shipping_id.state_id.id,
                    'tax_calc': 0,
                    'tax_rate_is': True
                })
        else:
            self.write({
                'shp_street': '',
                'shp_street2': '',
                'shp_zip': '',
                'shp_city': '',
                'shp_county': '',
                'shp_state_id': False,
                'tax_calc': 0,
                'tax_rate_is': True
            })
        if self.order_line and any(
                line.tax_status == 'yes' for line in self.order_line):
            total_tax = sum(
                line.unit_price * round(
                    self.tax_calc * line.product_uom_qty / 100, 2) for line in
                self.order_line if
                line.tax_status == 'yes')
            self.tax_amount_view = total_tax

    @api.onchange('partner_invoice_id')
    def _onchange_partner_invoice_id(self):
        if self.partner_invoice_id:
            self.write({
                'inv_street': self.partner_invoice_id.street,
                'inv_street2': self.partner_invoice_id.street2,
                'inv_zip': self.partner_invoice_id.zip,
                'inv_city': self.partner_invoice_id.city,
                'inv_county': self.partner_invoice_id.county,
                'inv_state_id': self.partner_invoice_id.state_id.id,
            })
        else:
            self.write({
                'inv_street': False,
                'inv_street2': False,
                'inv_zip': False,
                'inv_city': False,
                'inv_county': False,
                'inv_state_id': False,
            })

    @api.depends('order_line')
    def _compute_total_qty(self):
        """ Function to find total quantity in order_line"""
        for rec in self:
            rec.total_qty = 0
            if rec.order_line:
                total = sum(rec.order_line.mapped('product_uom_qty'))
                rec.write({'total_qty': total})

    @api.onchange('order_line')
    def _onchange_quantity(self):
        """ Function to update total quantity """
        qty = 0
        for rec in self.order_line:
            qty += rec.product_uom_qty * rec.product_uom.factor_inv
        self.total_product_quantity = qty

    @api.depends('order_line.discount', 'order_line.container_deposit_amount')
    def _compute_total_discount(self):
        """ Compute function to calculate the total discount amount and container deposit amount """
        for order in self:
            discount = container_deposit = 0.0
            for line in order.order_line:
                uom_qty = 1 / line.product_uom.factor
                discount += line.discount_amount
                container_deposit += uom_qty * line.product_uom_qty * line.product_id.container_deposit_amount if line.product_id.is_container_tax else 0
            order.update({
                'total_discount': discount,
                'total_container_deposit': container_deposit,
            })
            if order.total_discount_view and order.order_line:
                ls = order.order_line.mapped('product_uom_qty')
                if not all(val == ls[0] and val == 0 for val in ls):
                    diff = order.total_discount_view - order.total_discount
                    discount_line = diff / len(order.order_line.filtered(lambda
                                                                             l: l.product_uom_qty != 0 and l.product_id.product_type == 'product').mapped(
                        'id')) if len(order.order_line.filtered(lambda
                                                                    l: l.product_uom_qty != 0 and l.product_id.product_type == 'product').mapped(
                        'id')) > 0 else 0
                for line in order.order_line.filtered(
                        lambda p: p.product_id.product_type == 'product'):
                    line.diff_discount = False
                    if line.product_uom_qty != 0 and discount_line:
                        line.diff_discount = discount_line

    @api.onchange('total_container_deposit')
    def _onchange_total_container_deposit(self):
        """ fun to update container_deposit_view value"""
        self.write({'container_deposit_view': self.total_container_deposit})

    @api.onchange('total_discount')
    def _onchange_total_discount(self):
        """ based on total_discount the total_discount_view value is updated"""
        self.total_discount_view = self.total_discount

    @api.onchange('total_discount_view')
    def _onchange_total_discount_view(self):
        """ onchange fun based on total_discount_view """
        if self.order_line and self.total_discount_view:
            diff = self.total_discount_view - self.total_discount
            ls = self.order_line.mapped('product_uom_qty')
            if not all(val == ls[0] and val == 0 for val in ls):
                discount_line = diff / len(self.order_line.filtered(
                    lambda l: l.product_uom_qty != 0).mapped('id'))
                for line in self.order_line.filtered(
                        lambda l: l.product_uom_qty != 0):
                    line.diff_discount = discount_line
        if self.total_discount_view > self.amount_untaxed:
            raise UserError(_('Discount cannot be greater than Subtotal'))

    @api.depends('order_line.price_subtotal',
                 'order_line.price_total', 'insurance', 'shipping_handling',
                 'total_discount',
                 'container_deposit_view', 'tax_amount_view',
                 'total_discount_view')
    def _compute_amounts(self):
        """Compute the total amounts of the SO."""
        AccountTax = self.env['account.tax']
        for order in self:
            order_lines = order.order_line.filtered(
                lambda x: not x.display_type)
            base_lines = [line._prepare_base_line_for_taxes_computation() for
                          line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines,
                                                      order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines,
                                                     order.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            order.amount_untaxed = tax_totals['base_amount_currency']
            order.amount_tax = order.tax_amount_view = round(sum(
                    order_lines.mapped('tax_price')), 2)
            order.amount_total = (order.amount_untaxed + order.tax_amount_view
                                  + order.insurance + order.shipping_handling
                                  + order.container_deposit_view - order.total_discount_view)

    def _prepare_delivery_line_vals(self, carrier, unit_price):
        """replace the addon function to change price_unit field """
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            context['lang'] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)
        # Apply fiscal position
        taxes = carrier.product_id.taxes_id._filter_taxes_by_company(
            self.company_id)
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes).ids
        # Create the sales order line
        if carrier.product_id.description_sale:
            so_description = '%s: %s' % (carrier.name,
                                         carrier.product_id.description_sale)
        else:
            so_description = carrier.name
        values = {
            'order_id': self.id,
            'name': so_description,
            'price_unit': unit_price,
            'product_uom_qty': 1,
            'product_uom': carrier.product_id.uom_id.id,
            'product_id': carrier.product_id.id,
            'tax_id': [(6, 0, taxes_ids)],
            'is_delivery': True,
        }
        if carrier.free_over and self.currency_id.is_zero(unit_price):
            values['name'] = _('%s\nFree Shipping', values['name'])
        if self.order_line:
            values['sequence'] = self.order_line[-1].sequence + 1
        del context
        return values

    def _create_delivery_line(self, carrier, unit_price):
        """ replace the function to change price_unit field """
        values = self._prepare_delivery_line_vals(carrier, unit_price)
        return self.env['sale.order.line'].sudo().create(values)

    def write(self, values):
        res = super(CustomerSaleOrder, self).write(values)
        if self.env.context.get('params', {}).get(
                'view_type') == 'form' and 'tax_rate_is' not in values and 'tax_calc' not in values:
            for rec in self:
                if values.get('shp_street'):
                    street_changed = 'yes'
                else:
                    street_changed = 'no'
                if values.get('shp_city'):
                    city_changed = 'yes'
                else:
                    city_changed = 'no'
                if values.get('shp_zip'):
                    zip_changed = 'yes'
                else:
                    zip_changed = 'no'
                if values.get('shp_state_id'):
                    state_id_changed = 'yes'
                else:
                    state_id_changed = 'no'
                if values.get('tax_calc'):
                    if values['tax_calc'] <= 0:
                        tax_calc_zero = 'no'
                    else:
                        tax_calc_zero = 'yes'
                else:
                    tax_calc_zero = 'yes'
                if any((zip_changed == 'yes', state_id_changed == 'yes',
                        street_changed == 'yes',
                        city_changed == 'yes',
                        tax_calc_zero == 'yes')) and rec.shp_street and rec.shp_zip:
                    partner_given = self.env['res.partner'].sudo().browse(
                        values.get('partner_id'))
                    partner_delivery = self.env['res.partner'].sudo().search(
                        [('id', 'in', partner_given.child_ids.ids),
                         ('type', '=', 'delivery'),
                         ('zip', '=', rec.shp_zip),
                         ('city', '=', rec.shp_city),
                         ('street', '=', rec.shp_street),
                         ('state_id', '=', rec.shp_state_id.id),
                         ('tax_calc', '>', 0)])
                    partner_parent_delivery = self.env[
                        'res.partner'].sudo().search(
                        [('id', 'in', partner_given.parent_id.child_ids.ids),
                         ('type', '=', 'delivery'),
                         ('zip', '=', rec.shp_zip), ('city', '=', rec.shp_city),
                         ('street', '=', rec.shp_street),
                         ('state_id', '=', rec.shp_state_id.id),
                         ('tax_calc', '>', 0)])
                    delivery_address = partner_delivery if partner_delivery else partner_parent_delivery
                    delivery_address_exists = 0
                    if delivery_address and any(
                            address.tax_calc != 0 for address in
                            delivery_address):
                        for shipping in delivery_address:
                            if shipping:
                                delivery_address_exists = 1
                                rec.tax_calc = shipping.tax_calc
                                rec.tax_rate_is = False
                                break
                    if not delivery_address_exists:
                        tax_calc = 0
                        related_partner = self.env['res.partner'].sudo().search(
                            [('zip', '=', rec.shp_zip),
                             ('city', '=', rec.shp_city),
                             ('street', '=', rec.shp_street),
                             ('state_id', '=', rec.shp_state_id.id),
                             ('tax_calc', '>', 0)], limit=1)
                        related_warehouse = self.env[
                            'stock.warehouse'].sudo().search(
                            [('zip', '=', rec.shp_zip),
                             ('city', '=', rec.shp_city),
                             ('street', '=', rec.shp_street),
                             ('state_id', '=', rec.shp_state_id.id),
                             ('sales_tax', '!=', 0)], limit=1)
                        if related_partner.tax_calc and related_partner.tax_calc > 0:
                            tax_calc = related_partner.tax_calc
                        elif related_warehouse.sales_tax and related_warehouse.sales_tax > 0:
                            tax_calc = related_warehouse.sales_tax
                        else:
                            zip = '{:0>5}'.format(rec.shp_zip)
                            config_parm = self.env['ir.config_parameter'].sudo()
                            cart_items = [{"Qty": 1, "Price": 100, "TIC": '',
                                           "ItemID": 'mm'}]
                            lookup_data = {
                                "apiLoginID": config_parm.get_param(
                                    'tax_cloud_id'),
                                "apiKey": config_parm.get_param(
                                    'tax_cloud_key'),
                                "customerID": rec.name,
                                "deliveredBySeller": True,
                                "cartID": "",
                                "destination": {
                                    "Address1": rec.shp_street,
                                    "City": rec.shp_city,
                                    "State": rec.shp_state_id.code,
                                    "Zip5": zip,
                                    "Zip4": ''
                                },
                                "origin": {
                                    "Address1": rec.shp_street,
                                    "City": rec.shp_city,
                                    "State": rec.shp_state_id.code,
                                    "Zip5": zip,
                                    "Zip4": ''
                                },
                                "cartItems": cart_items
                            }
                            lookup_info = self.action_lookup_tax_rate(
                                lookup_data)
                            if lookup_info['ResponseType'] != 0:
                                tax_resp = lookup_info.get('CartItemsResponse')

                                tax_calc = tax_resp[0]['TaxAmount']
                        if tax_calc:
                            rec.tax_calc = tax_calc
                            rec.tax_rate_is = False
                        else:
                            rec.tax_calc = 0
                            rec.tax_rate_is = True
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """ super create function"""
        res = super(CustomerSaleOrder, self).create(vals_list)
        sequence = self.env.ref('averigo_sales_order.averigo_seq_quotation')
        seq = sequence.with_company(res.company_id.id).next_by_code(
            "sale.quotation") or _(
            'New')
        res.name = seq
        shipping_info = res.partner_shipping_id
        if shipping_info.schedule_tax_id:
            res.tax_calc = shipping_info.schedule_tax_id.total_tax
            res.tax_type = 'scheduled'
            res.schedule_tax_id = shipping_info.schedule_tax_id.id
        return res

    def unlink(self):
        """ delete restriction for quotation/sale order """
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise UserError(
                    _('You can not delete a sent quotation or a confirmed sales order.'))
        return super(CustomerSaleOrder, self).unlink()


class SaleOrderLine(models.Model):
    """ inherits sale order line """
    _inherit = 'sale.order.line'
    _description = "Quotation/Order Line"

    product_code = fields.Char(
        'Product Code', related='product_id.default_code', store=True)
    desc = fields.Text(
        'Description')
    internal_msg = fields.Text(
        'Internal Message')
    bin_location_id = fields.Many2one(
        'stock.location')
    bin_location_filter_ids = fields.Many2many(
        'stock.location', compute='_compute_bin_location_filter_ids')
    exclude_from_sale_order = fields.Boolean(
        help="Technical field used to exclude some lines from the"
             "order_line_ids tab in the form view.")
    sale_uom_ids = fields.Many2many(
        'uom.uom', compute='_compute_sale_uom_ids')
    weight = fields.Float(
        'Weight')
    tax_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], 'Taxable', default='yes')
    product_available_qty = fields.Float(
        'On Hand', compute='_compute_product_available_qty')
    unit_price = fields.Float(
        string='Price', required=True)
    gross_margin = fields.Float(
        'GM %', compute='_compute_gross_margin')
    product_cost = fields.Float(
        string='Cost', compute='_compute_cost', store=True)
    tax_price = fields.Float()
    diff_tax_amount = fields.Float()
    tax_amount_unit = fields.Float(
        store=True, compute='_compute_total_per_unit')
    container_deposit_amount = fields.Float(
        'Container Deposit')
    diff_container_amount = fields.Float(
        'Diff Container')
    container_amount_unit = fields.Float(
        store=True, compute='_compute_total_per_unit')
    discount_amount = fields.Float()
    diff_discount = fields.Float(
        'Diff Discount')
    discount_amount_unit = fields.Float(
        store=True, compute='_compute_total_per_unit')
    convert_check = fields.Boolean(
        'convert')
    cp_code = fields.Char(
        string="CP Code", size=60)
    asso_products = fields.Boolean()
    is_suger_tax = fields.Boolean()
    is_fuel_charge = fields.Boolean()
    is_hazard_fee = fields.Boolean()
    is_subsidy = fields.Boolean()
    standard_price = fields.Float(
        string='Product Cost')

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        """ override addon function to remove default tax from sale order line"""
        lines_by_company = defaultdict(lambda: self.env['sale.order.line'])
        cached_taxes = {}
        for line in self:
            if line.product_type == 'combo':
                line.tax_id = False
                continue
            lines_by_company[line.company_id] += line
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = None
                if line.order_id.averigo_sale_order:
                    line.tax_id = False
                else:
                    if line.product_id:
                        taxes = line.product_id.taxes_id._filter_taxes_by_company(
                            company)
                    if not line.product_id or not taxes:
                        # Nothing to map
                        line.tax_id = False
                        continue
                    fiscal_position = line.order_id.fiscal_position_id
                    cache_key = (
                        fiscal_position.id, company.id, tuple(taxes.ids))
                    cache_key += line._get_custom_compute_tax_cache_key()
                    if cache_key in cached_taxes:
                        result = cached_taxes[cache_key]
                    else:
                        result = fiscal_position.map_tax(taxes)
                        cached_taxes[cache_key] = result
                    # If company_id is set, always filter taxes by the company
                    line.tax_id = result

    @api.depends('product_id')
    def _compute_sale_uom_ids(self):
        """ to get different uom of a product"""
        for rec in self:
            uom_ids = [rec.product_id.uom_id.id]
            convert_uom_ids = rec.product_id.product_uom_ids.mapped(
                'convert_uom').ids
            uom_ids.extend(convert_uom_ids)
            rec.write({'sale_uom_ids': uom_ids})

    @api.depends('order_id.warehouse_id')
    def _compute_bin_location_filter_ids(self):
        """ to get bin location in sale order line"""
        for rec in self:
            rec.bin_location_filter_ids = None
            if rec.order_id.warehouse_id:
                location = rec.order_id.warehouse_id.lot_stock_id
                bin_location = self.env['stock.location'].sudo().search(
                    [('warehouse_id', '=', rec.order_id.warehouse_id.id),
                     ('is_bin_location', '=', True)])
                rec.bin_location_filter_ids = bin_location | location

    @api.depends('order_id.warehouse_id')
    def _compute_product_available_qty(self):
        """ to get product available qty"""
        for rec in self:
            parent_quant_source = self.env['stock.quant'].sudo().search(
                [('product_id', '=', rec.product_id.id), (
                    'location_id.warehouse_id.location_type', '=', 'view'),
                 ('location_id.usage', '=', 'internal')])
            rec.product_available_qty += sum(
                parent_quant_source.mapped('inventory_quantity'))

    @api.depends('product_id')
    def _compute_cost(self):
        """ to compute cost"""
        for rec in self:
            if rec.product_uom and rec.product_uom == rec.product_id.uom_id:
                rec.product_cost = rec.product_id.standard_price
            else:
                rec.product_cost = (
                                           1 / rec.product_uom.factor) * rec.product_id.standard_price

    @api.depends('unit_price', 'product_cost')
    def _compute_gross_margin(self):
        """ to compute gross margin"""
        for rec in self:
            if rec.unit_price > 0:
                rec.gross_margin = ((
                                            rec.unit_price - rec.product_cost) / rec.unit_price) * 100
            else:
                rec.gross_margin = (rec.unit_price - rec.product_cost) * 100

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'unit_price',
                 'tax_id')
    def _compute_amount(self):
        """ overrides the addon Compute the amounts of the SO line based on unit_price too"""
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line,
                                                                  line.company_id)
            line.price_subtotal = base_line['tax_details'][
                'raw_total_excluded_currency']
            line.price_total = base_line['tax_details'][
                'raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    @api.depends('diff_discount', 'product_uom_qty', 'diff_container_amount',
                 'product_id',
                 'discount_amount', 'container_deposit_amount', 'tax_price',
                 'diff_tax_amount')
    def _compute_total_per_unit(self):
        """ compute total per qty"""
        for rec in self:
            if rec.product_uom_qty != 0:
                rec.container_amount_unit = (
                                                    rec.container_deposit_amount + rec.diff_container_amount) / rec.product_uom_qty
                rec.discount_amount_unit = (
                                                   rec.discount_amount + rec.diff_discount) / rec.product_uom_qty
                rec.tax_amount_unit = rec.tax_price / rec.product_uom_qty
            else:
                rec.container_amount_unit = 0
                rec.discount_amount_unit = 0
                rec.tax_amount_unit = 0

    @api.onchange('product_id', 'product_uom')
    def _onchange_product_id(self):
        """ onchange fun based on product and product uom"""
        self.desc = self.product_id.description_sale
        self.bin_location_id = self.product_id.primary_location.id
        partner = self.order_id.partner_id
        if partner:
            list_1 = []
            list_2 = []
            product_lines = partner.sudo().mapped('customer_product_ids')
            if product_lines:
                for product_line in product_lines:
                    list_1.append(product_line.product_id.id)
                    list_2.append(product_line.uom_id.id)
                if self.product_id.id in list_1 and self.product_uom.id in list_2:
                    product_ids = self.env['customer.product'].sudo().search(
                        [('product_id', '=', self.product_id.id),
                         ('uom_id', '=', self.product_uom.id)])
                    for product_id in product_ids:
                        self.unit_price = product_id.list_price_1
                        self.tax_status = product_id.tax_status
                elif self.product_id.id in list_1 and self.product_uom.id not in list_2:
                    uom = self.product_id.product_uom_ids.filtered(
                        lambda s: s.convert_uom.id == self.product_uom.id)
                    if not uom:
                        if not partner.price_category:
                            self.unit_price = self.product_id.list_price_1
                        elif partner.price_category == 'list_price_1':
                            self.unit_price = self.product_id.list_price_1
                        elif partner.price_category == 'list_price_2':
                            self.unit_price = self.product_id.list_price_2
                        elif partner.price_category == 'list_price_3':
                            self.unit_price = self.product_id.list_price_3
                    elif partner.price_category == 'list_price_1':
                        self.unit_price = uom.sale_price_1
                    elif partner.price_category == 'list_price_2':
                        self.unit_price = uom.sale_price_2
                    elif partner.price_category == 'list_price_3':
                        self.unit_price = uom.sale_price_3
                    elif not partner.price_category:
                        self.unit_price = uom.sale_price_1
                elif self.product_id.id not in list_1 and partner.price_category == 'list_price_1':
                    self.unit_price = self.product_id.list_price_1
                    self.tax_status = self.product_id.tax_status
                elif self.product_id.id not in list_1 and partner.price_category == 'list_price_2':
                    self.unit_price = self.product_id.list_price_2
                    self.tax_status = self.product_id.tax_status
                elif self.product_id.id not in list_1 and partner.price_category == 'list_price_3':
                    self.unit_price = self.product_id.list_price_3
                    self.tax_status = self.product_id.tax_status
                elif self.product_id.id not in list_1 and partner.price_category == False:
                    if self.product_id.uom_id == self.product_uom:
                        if partner.price_category == 'list_price_1':
                            self.unit_price = self.product_id.list_price_1
                        elif partner.price_category == 'list_price_2':
                            self.unit_price = self.product_id.list_price_2
                        elif partner.price_category == 'list_price_3':
                            self.unit_price = self.product_id.list_price_3
                        elif not partner.price_category:
                            self.unit_price = self.product_id.list_price_1
                        self.tax_status = self.product_id.tax_status
                    elif len(self.product_id.product_uom_ids) > 0:
                        uom = self.product_id.product_uom_ids.filtered(
                            lambda s: s.convert_uom.id == self.product_uom.id)
                        if partner.price_category == 'list_price_1':
                            self.unit_price = uom.sale_price_1
                        elif partner.price_category == 'list_price_2':
                            self.unit_price = uom.sale_price_2
                        elif partner.price_category == 'list_price_3':
                            self.unit_price = uom.sale_price_3
                        elif not partner.price_category:
                            self.unit_price = uom.sale_price_1
                        self.tax_status = self.product_id.tax_status
                    else:
                        self.unit_price = self.product_id.list_price_1
            elif not product_lines and partner.price_category:
                uom = self.product_id.product_uom_ids.filtered(
                    lambda s: s.convert_uom.id == self.product_uom.id)
                if not uom:
                    if partner.price_category == 'list_price_1':
                        self.unit_price = self.product_id.list_price_1
                    elif partner.price_category == 'list_price_2':
                        self.unit_price = self.product_id.list_price_2
                    elif partner.price_category == 'list_price_3':
                        self.unit_price = self.product_id.list_price_3
                elif partner.price_category == 'list_price_1':
                    self.unit_price = uom.sale_price_1
                elif partner.price_category == 'list_price_2':
                    self.unit_price = uom.sale_price_2
                elif partner.price_category == 'list_price_3':
                    self.unit_price = uom.sale_price_3
            elif not (product_lines and partner.price_category):
                uom = self.product_id.product_uom_ids.filtered(
                    lambda s: s.convert_uom.id == self.product_uom.id)
                if uom:
                    self.unit_price = uom.sale_price_1
                else:
                    self.unit_price = self.product_id.list_price_1
        else:
            self.unit_price = self.product_id.list_price_1
            self.tax_status = self.product_id.tax_status
        if self.product_id in self.order_id.partner_id.customer_product_ids.sudo().mapped(
                'product_id'):
            cust_product_line = self.order_id.partner_id.customer_product_ids.sudo().filtered(
                lambda
                    s: s.product_id.id == self.product_id.id and s.uom_id.id == self.product_uom.id)
            self.cp_code = cust_product_line.cp_code

    @api.onchange('discount_amount')
    def _onchange_discount_amount(self):
        """ warning if discount greater than subtotal"""
        if self.discount_amount > self.price_subtotal:
            raise UserError(_('Discount cannot be greater than Subtotal'))

    @api.onchange('product_uom_qty', 'unit_price', 'tax_status')
    def _onchange_tax_amount(self):
        """ based on qty, price and tax calculating tax/container deposit amount"""
        self.tax_price = (
                                 self.product_uom_qty * self.unit_price * self.order_id.tax_calc) / 100 if self.tax_status == 'yes' else 0
        uom_qty = 1 / self.product_uom.factor
        self.container_deposit_amount = uom_qty * self.product_uom_qty * self.product_id.container_deposit_amount if self.product_id.is_container_tax else 0

    @api.model_create_multi
    def create(self, vals_list):
        """ override create function of sale order line"""
        res = super(SaleOrderLine, self).create(vals_list)
        for line in res:
            line.tax_price = (
                                         line.product_uom_qty * line.unit_price * line.order_id.tax_calc) / 100 if line.tax_status == 'yes' else 0
            if any((line.is_suger_tax, line.is_fuel_charge, line.is_hazard_fee,
                    line.is_subsidy)):
                line.order_id.tax_amount_view += line.tax_price
                line.tax_amount_unit = line.tax_price
                line.diff_tax_amount = line.tax_price
            line.container_deposit_amount = line.product_uom_qty * line.product_id.container_deposit_amount if line.product_id.is_container_tax else 0
            line.order_id.container_deposit_view = line.order_id.total_container_deposit
        return res


class AccountTaxInherit(models.Model):
    """Inherit account tax model to compute price based on unit_price"""
    _inherit = 'account.tax'

    @api.model
    def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
        """ Convert any representation of a business object ('record') into a base line being a python
        dictionary that will be used to use the generic helpers for the taxes computation.

        The whole method is designed to ease the conversion from a business record.
        For example, when passing either account.move.line, either sale.order.line or purchase.order.line,
        providing explicitely a 'product_id' in kwargs is not necessary since all those records already have
        an `product_id` field.

        :param record:  A representation of a business object a.k.a a record or a dictionary.
        :param kwargs:  The extra values to override some values that will be taken from the record.
        :return:        A dictionary representing a base line.
        """

        def load(field, fallback):
            return self._get_base_line_field_value_from_record(record, field,
                                                               kwargs, fallback)

        currency = (
                load('currency_id', None)
                or load('company_currency_id', None)
                or load('company_id', self.env['res.company']).currency_id
                or self.env['res.currency']
        )
        return {
            **kwargs,
            'record': record,
            'id': load('id', 0),
            # Basic fields:
            'product_id': load('product_id', self.env['product.product']),
            'tax_ids': load('tax_ids', self.env['account.tax']),
            'price_unit': load('unit_price', 0.0) or load('price_unit', 0.0),
            'quantity': load('quantity', 0.0),
            'discount': load('discount', 0.0),
            'currency_id': currency,
            # The special_mode for the taxes computation:
            # - False for the normal behavior.
            # - total_included to force all taxes to be price included.
            # - total_excluded to force all taxes to be price excluded.
            'special_mode': kwargs.get('special_mode', False),
            # A special typing of base line for some custom behavior:
            # - False for the normal behavior.
            # - early_payment if the base line represent an early payment in mixed mode.
            # - cash_rounding if the base line is a delta to round the business object for the cash rounding feature.
            'special_type': kwargs.get('special_type', False),
            # All computation are managing the foreign currency and the local one.
            # This is the rate to be applied when generating the tax details (see '_add_tax_details_in_base_line').
            'rate': load('rate', 1.0),
            # For all computation that are inferring a base amount in order to reach a total you know in advance, you have to force some
            # base/tax amounts for the computation (E.g. down payment, combo products, global discounts etc).
            'manual_tax_amounts': kwargs.get('manual_tax_amounts', None),
            # ===== Accounting stuff =====
            # The sign of the business object regarding its accounting balance.
            'sign': load('sign', 1.0),
            # If the document is a refund or not to know which repartition lines must be used.
            'is_refund': load('is_refund', False),
            # If the tags must be inverted or not.
            'tax_tag_invert': load('tax_tag_invert', False),
            # Extra fields for tax lines generation:
            'partner_id': load('partner_id', self.env['res.partner']),
            'account_id': load('account_id', self.env['account.account']),
            'analytic_distribution': load('analytic_distribution', None),
        }
