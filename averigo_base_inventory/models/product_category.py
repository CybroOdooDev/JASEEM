# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductCategory(models.Model):
    """Extends the Odoo Product Category model to include additional fields and functionalities."""
    _name = "product.category"
    _inherit = ['product.category', 'mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(
        string='active', default=True)
    company_id = fields.Many2one(
        comodel_name="res.company", string='company', required=True, default=lambda self: self.env.company)
    category_code = fields.Char(
        copy=False)
    category_image_1920 = fields.Image()
    category_desc = fields.Text(
        string='Description')
    enable_front_desk = fields.Boolean(
        string='Enable Front Desk')
    available_outside = fields.Boolean(
        string="Available Outside Market Area",default=False)
    update_image = fields.Char(
        default='0')
    internal_reference = fields.Char(
        string="SAP Category No", tracking=True)
    exclude_from_sale = fields.Boolean(
        string='Exclude from VMS Sales')
    beer_and_wine = fields.Boolean(
        string="Is this a Category for Beer & Wine Products?")

    _sql_constraints = [("category_code", "unique(category_code, company_id)",
                         "The code you entered is already taken, please try a new one"),
                        ("product_category_name_operator_unique", "unique(name, company_id)",
                         "There is an existing category with same name")]

    def write(self, vals):
        """Override the write method to update the `update_image` field when the category image is changed."""
        res = super().write(vals)
        if 'category_image_1920' in vals:
            self.update_image = '0' + self.update_image
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """Override the copy method to ensure the copied category has a unique name."""
        default = dict(default or {})
        default.update(
            name=_("%s (copy)") % (self.name or ''))
        return super(ProductCategory, self).copy(default)
