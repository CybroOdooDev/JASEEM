# -*- coding: utf-8 -*-
from odoo import models, fields, api


class UoMCustomTypes(models.Model):
    """Model representing custom UoM (Unit of Measure) types."""
    _name = "custom.uom.types"
    _description = "Custom UOM Types"

    name = fields.Char(
        'Name', required=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

    _sql_constraints = [("name", "unique(name, company_id)", "Name must be unique!")]


class ProductUoM(models.Model):
    """Class for the model multiple_uom"""
    _name = "multiple.uom"
    _description = 'Product Multiple UoM'

    uom_template_id = fields.Many2one(
        'product.template', 'UoM', index=True)
    convert_uom = fields.Many2one(
        'uom.uom', 'Convert UoM', required=True)
    quantity = fields.Integer(
        string='Quantity',default=1)
    standard_price = fields.Float(
        string='Cost', compute='_compute_standard_prices')
    sale_price_1 = fields.Float(
        'Sales Price 1', digits='Product Price')
    sale_price_2 = fields.Float(
        'Sales Price 2', digits='Product Price')
    sale_price_3 = fields.Float(
        'Sales Price 3', digits='Product Price')
    name = fields.Char(
        string="Name")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)
    type = fields.Many2one(
        'custom.uom.types', string='UoM',
        required=True,domain="[('company_id', '=', company_id)]")


    @api.depends('uom_template_id.standard_price')
    def _compute_standard_prices(self):
        """Computing the standard price based on quantity and product price while changing product price"""
        for rec in self:
            rec.standard_price = rec.quantity * rec.uom_template_id.standard_price

    @api.onchange('quantity')
    def _onchange_standard_prices(self):
        """Computing the standard price based on quantity and product price while changing quantity"""
        for rec in self:
            rec.standard_price = rec.quantity * rec._origin.uom_template_id.standard_price

    @api.onchange('type')
    def onchange_type(self):
        """Update the `name` field based on the selected `type`."""
        if self.type:
            self.name = self.type.name

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new UoM record with the specified details."""
        for vals in vals_list:
            if not vals.get('name') or not vals.get('quantity') or not vals.get('uom_template_id'):
                raise ValueError("Missing required fields: 'name', 'quantity', or 'uom_template_id'")
            var = f"{vals.get('name')} ({vals.get('quantity')})"
            domain = [
                ('name', '=', var),
                ('company_id', '=', self.env.user.company_id.id)
            ]
            uom_name = self.env['uom.uom'].search(domain, limit=1)
            # To check that the UoM Type and Quantity already exist. UoM name is UoM Type + (Quantity)
            if uom_name:
                vals['convert_uom'] = uom_name.id
            else:
                try:
                    template = self.env['product.template'].browse(vals.get('uom_template_id'))
                    category_id = template.uom_id.category_id.id

                    convert_uom = self.env['uom.uom'].with_context(self.env.context).create([{
                        'name': var,
                        'uom_type': 'bigger',
                        'category_id': category_id,
                        'factor_inv': vals.get('quantity'),
                    }])
                    vals['convert_uom'] = convert_uom.id
                except Exception as e:
                    raise RuntimeError(f"Failed to create UoM: {e}")
        return super().create(vals_list)

    def write(self, vals):
        """Update an existing UoM record with the specified details."""
        var = ''
        if vals.get('type'):
            name = self.env['custom.uom.types'].search(
                [('id', '=', vals.get('type'))])
            if vals.get('quantity'):
                var = f"{name.name} ({vals.get('quantity')})"
                qty = vals.get('quantity')
            else:
                var = f"{name.name} ({self.quantity})"
                qty = self.quantity
            uom_name = self.env['uom.uom'].search([('name', '=', var)],
                                                  limit=1)
            # To check that the UoM Type and Quantity already exist. UoM name is UoM Type + (Quantity)
            if uom_name:
                vals['convert_uom'] = uom_name.id
            else:
                convert_uom = self.env['uom.uom'].with_context(
                    self.env.context).create([{
                    'name': var,
                    'uom_type': 'bigger',
                    'category_id': self.env['product.template'].search(
                        [('id', '=',
                          self.uom_template_id.id)]).uom_id.category_id.id,
                    'factor_inv': qty,

                }])
                vals['convert_uom'] = convert_uom.id
        elif vals.get('quantity'):
            var = f"{self.type.name} ({vals.get('quantity')})"
            qty = vals.get('quantity')
            uom_name = self.env['uom.uom'].search([('name', '=', var)],
                                                  limit=1)
            # To check that the UoM Type and Quantity already exist. UoM name is UoM Type + (Quantity)
            if uom_name:
                vals['convert_uom'] = uom_name.id
            else:
                convert_uom = self.env['uom.uom'].with_context(
                    self.env.context).create([{
                    'name': var,
                    'uom_type': 'bigger',
                    'category_id': self.env['product.template'].search(
                        [('id', '=',
                          self.uom_template_id.id)]).uom_id.category_id.id,
                    'factor_inv': qty,
                }])
                vals['convert_uom'] = convert_uom.id
        return super().write(vals)

class UomCategory(models.Model):
    """Inheriting the model uom_category"""
    _inherit = 'uom.category'

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)


class UomUom(models.Model):
    """Inheriting the model uom_uom"""
    _inherit = 'uom.uom'

    company_id = fields.Many2one(
        comodel_name='res.company', default=lambda self: self.env.company)

