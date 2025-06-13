# -*- coding: utf-8 -*-
import re
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CustomerProduct(models.Model):
    """Product Linked/Associated to Customer"""
    _inherit = 'customer.product'

    name = fields.Char(
        string="Description", related='product_id.name')
    uom_category = fields.Integer()
    uom_ids = fields.Many2many(
        'uom.uom', 'customer_product_uom_rel',
        string='Product UOMs', compute='_compute_multiple_uom_id')
    uom_id = fields.Many2one(
        'uom.uom', domain="[('category_id', '=', uom_category)]",
        tracking=True)
    tax_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], 'Taxable', tracking=True)
    order_type = fields.Many2one(
        'order.type', string='Order Types')
    list_price = fields.Float(
        'Price', readonly=False, tracking=True)
    item_cost = fields.Float(
        string='Cost', store=True, compute='_compute_item_cost')
    margin_price = fields.Float(
        string='Margin %')
    catalog_id = fields.Many2one(
        'product.catalog')
    catalog_price = fields.Float()
    price_status = fields.Char(
        compute='_compute_price_status')
    select_product = fields.Boolean(
        default=True)
    unit_ids = fields.Many2many(
        'uom.uom', 'customer_product_unit_rel',
        string='Product UOMs', compute='_compute_unit_ids')
    cp_code = fields.Char(
        string="CP Code", size=60)

    _sql_constraints = [("cp_code_uniq", "unique(cp_code, customer_product_id)",
                         "CP Code must be unique for Order Products!")]

    @api.onchange('cp_code')
    def _onchange_cp_code(self):
        """ cp code validation """
        regex = re.compile('[@_!#$%^*()<>?/|}{~:]')
        if self.cp_code:
            if regex.search(self.cp_code) is not None:
                raise UserError(
                    _("You cannot use special character for CP Code."))

    @api.depends('product_id.standard_price', 'uom_id')
    def _compute_item_cost(self):
        """ function to compute cost of product """
        for rec in self:
            rec.item_cost = rec.product_id.standard_price * rec.uom_id.factor_inv

    @api.depends('list_price')
    def _compute_price_status(self):
        """ function to compute price status """
        for rec in self:
            if rec.catalog_id:
                if rec.list_price == rec.catalog_price:
                    rec.price_status = 'Catalog - %s' % rec.catalog_id.name
                    if rec.list_price > 0:
                        margin = ((
                                              rec.list_price - rec.item_cost) / rec.list_price) * 100
                        if margin > 0:
                            rec.margin_price = margin
                        else:
                            rec.margin_price = 0
                else:
                    rec.price_status = 'Entered'
                    if rec.list_price > 0:
                        margin = ((
                                              rec.list_price - rec.item_cost) / rec.list_price) * 100
                        if margin > 0:
                            rec.margin_price = margin
                        else:
                            rec.margin_price = 0
            else:
                rec.price_status = 'Entered'
                if rec.list_price > 0:
                    margin = ((
                                          rec.list_price - rec.item_cost) / rec.list_price) * 100
                    if margin > 0:
                        rec.margin_price = margin
                    else:
                        rec.margin_price = 0

    @api.depends('product_id')
    def _compute_multiple_uom_id(self):
        """ function to compute multiple uom """
        for rec in self:
            multiple_uom_ids = self.env['multiple.uom'].search(
                [('uom_template_id', '=', rec.product_id.product_tmpl_id.id)])
            product_uom_ids = multiple_uom_ids.mapped(
                'convert_uom') + rec.product_id.uom_id
            uom_ids = product_uom_ids
            rec.uom_ids += uom_ids

    def _compute_unit_ids(self):
        """ function to filter uom"""
        partner = self.env['res.partner'].browse(
            self.customer_product_id._origin.id)
        self.unit_ids = False
        for rec in self:
            multiple_uom_ids = self.env['multiple.uom'].search(
                [('uom_template_id', '=', rec.product_id.product_tmpl_id.id)])
            customer_products = self.env['customer.product'].sudo().search(
                [('customer_product_id', '=', partner.id),
                 ('product_id', '=', rec.product_id.id)])
            product_uom_ids = multiple_uom_ids.mapped(
                'convert_uom') + rec.product_id.uom_id
            unit_ids = product_uom_ids - customer_products.mapped('uom_id')
            rec.unit_ids += unit_ids

    @api.onchange('list_price')
    def _onchange_list_price(self):
        """ fun to update list price """
        for rec in self:
            if rec.catalog_id:
                if rec.list_price == rec.catalog_price:
                    rec.price_status = 'Catalog - %s' % rec.catalog_id.name
                    if rec.list_price > 0:
                        margin = ((
                                              rec.list_price - rec.item_cost) / rec.list_price) * 100
                        if margin > 0:
                            rec.margin_price = margin
                        else:
                            rec.margin_price = 0
                else:
                    rec.price_status = 'Entered'
                    if rec.list_price > 0:
                        margin = ((
                                              rec.list_price - rec.item_cost) / rec.list_price) * 100
                        if margin > 0:
                            rec.margin_price = margin
                        else:
                            rec.margin_price = 0
            else:
                rec.price_status = 'Entered'
                if rec.list_price > 0:
                    margin = ((
                                          rec.list_price - rec.item_cost) / rec.list_price) * 100
                    if margin > 0:
                        rec.margin_price = margin
                    else:
                        rec.margin_price = 0

    @api.depends('uom_id')
    @api.onchange('uom_id')
    def get_uom_id(self):
        """ fun to get uom and update list price"""
        cust_list_price = self._origin.product_id.list_price
        for rec in self._origin.product_id.product_uom_ids:
            if rec.convert_uom == self.uom_id:
                self.item_cost = rec.standard_price
                if self.customer_product_id.price_category == 'list_price_1':
                    cust_list_price = rec.sale_price_1
                elif self.customer_product_id.price_category == 'list_price_2':
                    cust_list_price = rec.sale_price_2
                elif self.customer_product_id.price_category == 'list_price_3':
                    cust_list_price = rec.sale_price_3
                elif not self.customer_product_id.price_category:
                    cust_list_price = rec.sale_price_1
                self.list_price = cust_list_price
            elif self.uom_id == self.product_id.uom_id:
                self.item_cost = self.product_id.standard_price
                if self.customer_product_id.price_category == 'list_price_1':
                    cust_list_price = self.product_id.list_price_1
                elif self.customer_product_id.price_category == 'list_price_2':
                    cust_list_price = self.product_id.list_price_2
                elif self.customer_product_id.price_category == 'list_price_3':
                    cust_list_price = self.product_id.list_price_3
                elif not self.customer_product_id.price_category:
                    cust_list_price = self.product_id.list_price_1
                self.list_price = cust_list_price


class CustomerMultipleUom(models.Model):
    """Add Multiple UOM Products to Customer"""
    _name = "product.customer.uom"
    _description = 'Add Multiple UOM Products to Customer'

    partner_id = fields.Many2one(
        'res.partner')
    name = fields.Char(
        'Product')
    product_id = fields.Many2one(
        'product.product')
    uom_id = fields.Many2one(
        'uom.uom', string='UOM')
    uom_ids = fields.Many2many(
        'uom.uom', compute='_compute_multiple_uom_id', string='Product UOMs')
    multiple_uom_ids = fields.Many2many(
        'multiple.uom', compute='_compute_multiple_uom_id')
    multiple_uom_id = fields.Many2one(
        'multiple.uom')
    add_product = fields.Boolean(
        'Add', default=True)
    micro_market_ids = fields.Many2many(
        'stock.warehouse')

    @api.depends('product_id')
    def _compute_multiple_uom_id(self):
        """ fun to filter uom"""
        for rec in self:
            multiple_uom_ids = self.env['multiple.uom'].search(
                [('uom_template_id', '=', rec.product_id.product_tmpl_id.id)])
            customer_products = self.env['customer.product'].sudo().search(
                [('customer_product_id', '=', rec.partner_id.id),
                 ('product_id', '=', rec.product_id.id)])
            product_uom_ids = multiple_uom_ids.mapped(
                'convert_uom') + rec.product_id.uom_id
            uom_ids = product_uom_ids - customer_products.mapped('uom_id')
            rec.uom_ids += uom_ids
            rec.multiple_uom_ids += multiple_uom_ids

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        """ onchange fun to get multiple uom values"""
        multiple_uom = self.env['multiple.uom'].search(
            [('uom_template_id', '=', self.product_id.product_tmpl_id.id),
             ('convert_uom', '=', self.uom_id._origin.id)])
        self.multiple_uom_id = multiple_uom.id


class CustomerCatalog(models.Model):
    """Product from Selected Catalog"""
    _name = "catalog.customer"
    _description = 'Catalog Product in Customer'

    partner_id = fields.Many2one(
        'res.partner')
    catalog_id = fields.Many2one(
        'product.catalog')
    product_id = fields.Many2one(
        'product.product')
    categ_id = fields.Many2one(
        'product.category', 'Product Category', store=True,
        related='product_id.categ_id')
    select_product = fields.Boolean(
        'Add', default=True)
    name = fields.Char()
    product_code = fields.Char(
        'Product code')
    tax_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')], 'Taxable')
    list_price = fields.Float(
        'Price', readonly=False, digits='Product Price')
    item_cost = fields.Float(
        related='product_id.standard_price', string='Cost', store=True)
    uom_id = fields.Many2one(
        'uom.uom')
    margin_price = fields.Float(
        'Margin %')

    @api.onchange('list_price')
    def _onchange_list_price(self):
        """Updating margin"""
        if self.list_price > 0:
            margin = ((
                                  self.list_price - self.item_cost) / self.list_price) * 100
            if margin > 0:
                self.margin_price = margin
            else:
                self.margin_price = 0
        else:
            self.margin_price = 0
