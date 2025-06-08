# -*- coding: utf-8 -*-
from odoo import api, models, fields


class StockLocation(models.Model):
    """Class to inherit model stock_location for creating bin location"""
    _inherit = 'stock.location'
    _description = "Bin Location"

    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Location")
    max_pallets = fields.Integer(
        string="Max Pallets")
    height = fields.Float(
        string="Height")
    width = fields.Float(
        string="Width")
    depth = fields.Float(
        string="Depth")
    volume = fields.Float(
        string="Volume")
    is_bin_location = fields.Boolean(
        string="Bin Location")
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company)
    aisle = fields.Char(
        string="Aisle")
    bay = fields.Char(
        string="Bay")
    shelf = fields.Char(
        string="Shelf")
    bin = fields.Char(
        string="Bin")

    @api.depends('name', 'location_id.complete_name')
    def _compute_complete_name(self):
        """Function to compute the complete name of the bin location"""
        for location in self:
            if not self.is_bin_location:
                if location.location_id and location.usage != 'view':
                    location.complete_name = '%s/%s' % (location.location_id.complete_name, location.name)
                else:
                    location.complete_name = location.name
            else:
                if location.warehouse_id:
                    location.complete_name = '%s/%s' % (location.warehouse_id.code, location.name)
                else:
                    location.complete_name = location.name

    def write(self, vals):
        """Function to add the condition for warehouse and transit quantity"""
        res = super().write(vals)
        for rec in self:
            if rec.is_bin_location:
                if 'warehouse_id' in vals:
                    location_id = self.env['stock.warehouse'].search(
                        [('id', '=', vals['warehouse_id'])]).lot_stock_id.id
                    rec.location_id = location_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Function to fix import error"""
        res = super().create(vals_list)
        for vals in vals_list:
            if 'complete_name' in vals and 'name' not in vals:
                vals['name'] = vals['complete_name']
            if 'warehouse_id' in vals:
                location_id = self.env['stock.warehouse'].search(
                    [('id', '=', vals['warehouse_id'])]).lot_stock_id.id
                res.location_id = location_id
        return res
