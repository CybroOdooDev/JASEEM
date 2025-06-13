# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResPartnerInherit(models.Model):
    """inherit res partner model for associating products"""
    _inherit = 'res.partner'

    product_ids = fields.Many2many(
        'product.product',
        domain="[('type', 'in', ['consu'])]", string='Products')
    product_filter_ids = fields.Many2many(
        'product.product', 'catalog_filter_id',
        compute='_compute_product_filter_ids')
    catalog_ids = fields.Many2many(
        'product.catalog',
        domain="[('catalog_type', '=', 'customer')]", string='Product Catalog')
    product_catalog_ids = fields.Many2many(
        'product.product.catalog')
    catalog_product_ids = fields.One2many(
        'catalog.customer', 'partner_id')
    catalog_length = fields.Integer(
        string="Count", compute="_compute_cat_prod_count")
    select_catalog_products = fields.Boolean(
        'Select All', default=True)
    customer_product_ids = fields.One2many(
        'customer.product', 'customer_product_id',
        tracking=True, copy=True)
    product_count = fields.Integer(
        compute='_compute_product_count')
    multiple_uom_products = fields.One2many(
        'product.customer.uom', 'partner_id')
    product_select_uom_length = fields.Integer(
        string="Count", compute="_compute_product_select_uom_length")
    schedule_tax_id = fields.Many2one(
        'schedule.tax')

    @api.depends('catalog_product_ids', 'catalog_length')
    def _compute_cat_prod_count(self):
        """Get catalog products length"""
        for rec in self:
            rec.catalog_length = len(rec.catalog_product_ids)

    @api.onchange('select_catalog_products')
    def _onchange_select_all(self):
        """To select all the products in the list"""
        if self.select_catalog_products:
            for catalog_product_id in self.catalog_product_ids:
                catalog_product_id.select_product = True
        else:
            for catalog_product_id in self.catalog_product_ids:
                catalog_product_id.select_product = False

    def reset(self):
        """ to reset the associated products from catalog"""
        self.product_ids = None
        self.catalog_ids = None
        self.catalog_product_ids = [(5, 0, 0)]
        self.select_catalog_products = True

    @api.onchange('catalog_ids')
    def _onchange_catalog_ids(self):
        """get the product list from product catalog """
        exist_product = self.customer_product_ids.mapped('product_id').ids
        product_ids = self.catalog_ids.catalog_product_ids
        customer_catalog = []
        for product_id in product_ids:
            self.product_catalog_ids += product_id
            product = product_id.product_id.id
            if product not in exist_product:
                dic = {
                    'product_id': product,
                    'name': product_id.product_id.name,
                    'catalog_id': product_id.catalog_id.id,
                    'product_code': product_id.product_code,
                    'uom_id': product_id.uom_id.id,
                    'categ_id': product_id.categ_id.id,
                    'tax_status': product_id.tax_status,
                    'list_price': product_id.list_price,
                    'item_cost': product_id.product_id.standard_price,
                }
                if product_id.list_price > 0:
                    margin = ((
                                      product_id.list_price - product_id.product_id.standard_price) / product_id.list_price) * 100
                    if margin > 0:
                        dic.update({'margin_price': margin})
                    else:
                        dic.update({'margin_price': 0})
                else:
                    dic.update({
                        'margin_price': 0,
                    })
                vals = (0, 0, dic)
                customer_catalog.append(vals)
        self.catalog_product_ids = [(2, 0, 0)] + customer_catalog

    def add_product_catalog(self):
        """ Add catalog products"""
        products = self.catalog_product_ids
        product_list = []
        for product in products:
            multiple_uom_ids = self.env['multiple.uom'].search(
                [('uom_template_id', '=', product.id)])
            product_uom_ids = multiple_uom_ids.mapped(
                'convert_uom') + product.uom_id
            exist_product = self.customer_product_ids.mapped('product_id').ids
            if product.select_product:
                if product.product_id.id not in exist_product:
                    vals = (0, 0, {
                        'product_id': product.product_id.id,
                        'name': product.name,
                        'product_code': product.product_code,
                        'uom_id': product.uom_id.id,
                        'uom_ids': product_uom_ids,
                        'catalog_id': product.catalog_id.id,
                        'tax_status': product.tax_status,
                        'list_price': product.list_price,
                        'catalog_price': product.list_price,
                        'item_cost': product.item_cost,
                        'margin_price': product.margin_price,
                    })
                    product_list.append(vals)
        self.customer_product_ids = [(2, 0, 0)] + product_list
        self.product_ids = None
        self.catalog_ids = None
        self.catalog_product_ids = None
        self.select_catalog_products = True

    def _compute_product_count(self):
        """Function to compute the number of product in the order_line"""
        for rec in self:
            rec.product_count = len(rec.sudo().customer_product_ids)

    @api.depends('customer_product_ids')
    def _compute_product_filter_ids(self):
        """ to get products based customer products"""
        for rec in self:
            rec.product_filter_ids = None
            products = rec.customer_product_ids.sudo().mapped('product_id')
            for product in products:
                if not product.product_uom_ids:
                    rec.product_filter_ids += product
                elif len(product.product_uom_ids) > 0:
                    product_uom = product.product_uom_ids.mapped('convert_uom')
                    customer_products = self.env[
                        'customer.product'].sudo().search(
                        [('customer_product_id', '=', rec.id),
                         ('product_id', '=', product.id)])
                    uom_length = product_uom + product.uom_id
                    cat_uom = customer_products.mapped('uom_id')
                    uom_lst = []
                    for uom in uom_length:
                        if uom not in cat_uom:
                            uom_lst.append(uom)
                    if not uom_lst:
                        rec.product_filter_ids += product

    def add_product(self):
        """ Add products to Customer Product"""
        products = self.product_ids
        exist_product_check = self.customer_product_ids.sudo().mapped(
            'product_id').ids
        exist_product = self.product_filter_ids.ids
        product_list = []
        product_uom_lists = []
        for product in products:
            if product.id in exist_product_check:
                vals = (0, 0, {
                    'product_id': product.id})
                product_uom_lists.append(vals)
            elif product.id not in exist_product:
                dic = {
                    'product_id': product.id,
                    'name': product.name,
                    'product_code': product.default_code,
                    'uom_id': product.uom_id.id,
                    'tax_status': product.tax_status,
                    'item_cost': product.standard_price,
                }
                cust_list_price = 0
                if self.price_category == 'list_price_1':
                    cust_list_price = product.list_price_1
                elif self.price_category == 'list_price_2':
                    cust_list_price = product.list_price_2
                elif self.price_category == 'list_price_3':
                    cust_list_price = product.list_price_3
                elif not self.price_category:
                    cust_list_price = product.list_price_1
                dic.update({
                    'list_price': cust_list_price, })
                if product.list_price_1 > 0 and cust_list_price != 0:
                    margin = ((
                                      cust_list_price - product.standard_price) / cust_list_price) * 100
                    if margin > 0:
                        dic.update({'margin_price': margin})
                    else:
                        dic.update({'margin_price': 0})
                else:
                    dic.update({'margin_price': 0})
                vals = (0, 0, dic)
                product_list.append(vals)
                self.product_filter_ids += product
        self.multiple_uom_products = [(2, 0, 0)] + product_uom_lists
        self.customer_product_ids = [(2, 0, 0)] + product_list
        self.product_ids = None

    @api.depends('multiple_uom_products', 'product_select_uom_length')
    def _compute_product_select_uom_length(self):
        """ fun to calculate count of uom"""
        for rec in self:
            rec.product_select_uom_length = len(rec.multiple_uom_products)

    def add_multiple_uom_product(self):
        """ Add products with different UOM"""
        products = self.multiple_uom_products
        product_list = []
        for product in products:
            if product.add_product:
                if not product.uom_id:
                    raise UserError(_('UOM is not selected'))
                else:
                    dic = {
                        'product_id': product.product_id.id,
                        'name': product.product_id.name,
                        'product_code': product.product_id.default_code,
                        'tax_status': product.product_id.tax_status,
                        'item_cost': product.multiple_uom_id.standard_price,
                        'uom_id': product.uom_id.id, }
                    if self.price_category == 'list_price_1':
                        dic.update({
                            'list_price': product.multiple_uom_id.sale_price_1 if product.multiple_uom_id else product.product_id.list_price_1,
                        })
                    elif self.price_category == 'list_price_2':
                        dic.update({
                            'list_price': product.multiple_uom_id.sale_price_2 if product.multiple_uom_id else product.product_id.list_price_2,
                        })
                    elif self.price_category == 'list_price_3':
                        dic.update({
                            'list_price': product.multiple_uom_id.sale_price_3 if product.multiple_uom_id else product.product_id.list_price_3,
                        })
                    elif not self.price_category:
                        dic.update({
                            'list_price': product.multiple_uom_id.sale_price_1 if product.multiple_uom_id else product.product_id.list_price_1,
                        })
                    if dic.get('list_price') > 0:
                        margin = ((dic.get(
                            'list_price') - product.multiple_uom_id.standard_price) / dic.get(
                            'list_price')) * 100
                        if margin >= 0:
                            dic.update(
                                {'margin_price': margin, })
                        else:
                            dic.update(
                                {'margin_price': 0, })
                    else:
                        dic.update(
                            {'margin_price': 0, })
                    vals = (0, 0, dic)
                    product_list.append(vals)
                    self.product_filter_ids += product.product_id
        self.customer_product_ids = [(2, 0, 0)] + product_list
        self.multiple_uom_products = None
        self.product_ids = None

    def cancel_multiple_uom_product(self):
        """ fun to reset the values when click on cancel button"""
        self.multiple_uom_products = None
        self.product_ids = None

    def unlink(self):
        """ unlink action for customer"""
        sale_order = self.env['sale.order'].search(
            ['|', '|', ('partner_id', 'in', self.ids),
             ('partner_invoice_id', 'in', self.ids),
             ('partner_shipping_id', 'in', self.ids)])
        if sale_order:
            raise UserError(
                _('You cannot delete the Customer. There is Sale order associated with the Customer / Billing Address / Delivery Address'))
        return super(ResPartnerInherit, self).unlink()
