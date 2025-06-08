# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StockQuantExt(models.Model):
    """class to inherit stock_quant model"""
    _inherit = 'stock.quant'

    warehouse_id = fields.Many2one(
        'stock.warehouse', 'Location',
        compute='compute_warehouse_id', inverse='get_location_id')
    location_id = fields.Many2one(
        'stock.location', 'Location Stock',
        domain=lambda self: self._domain_location_id(),
        auto_join=True, ondelete='restrict', readonly=True, required=True,
        index=True, check_company=True)
    quantity = fields.Float(
        'Quantity',
        help='Quantity of products in this quant, in the default unit of measure of the product',
        readonly=True, digits='Product Unit of Measure')
    inventory_quantity = fields.Float(
        'Inventoried Quantity', compute='_compute_inventory_quantity',
        inverse='_set_inventory_quantity',
        digits='Product Unit of Measure')
    reserved_quantity = fields.Float(
        'Reserved Quantity', default=0.0,
        help='Quantity of reserved products in this quant, in the default unit of measure of the product',
        readonly=True, required=True, digits='Product Unit of Measure')

    @api.onchange('warehouse_id')
    def get_location_id(self):
        """Function for getting location"""
        self.location_id = self.warehouse_id.lot_stock_id.id

    def compute_warehouse_id(self):
        """Function for computing warehouse id"""
        for rec in self:
            if rec.location_id.is_bin_location:
                rec.warehouse_id = rec.location_id.warehouse_id.id
            else:
                rec.warehouse_id = self.env['stock.warehouse'].search(
                    [('lot_stock_id', '=', rec.location_id.id)])

    @api.model
    def _get_inventory_fields_create(self):
        """Function to returns a list of fields user can edit when he want to create a quant in `inventory_mode`."""
        return ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id',
                'inventory_quantity', 'warehouse_id']

    @api.depends('quantity')
    def _compute_inventory_quantity(self):
        """Function to compute inventory quantity"""
        for quant in self:
            quant.inventory_quantity = quant.quantity
