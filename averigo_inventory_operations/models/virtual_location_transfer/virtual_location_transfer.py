# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class VirtualLocationTransfer(models.Model):
    """Virtual Location"""
    _name = 'virtual.location.transfer'
    _inherit = ['mail.thread']
    _description = 'Virtual Location Stock Transfer'
    _order = 'name desc'

    name = fields.Char(
        default='New')
    sequence = fields.Char(
        string="Sequence")
    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Warehouse",
        domain=[('location_type', '=', 'view')])
    # ('is_parts_warehouse', '!=', True)])
    warehouse_to_id = fields.Many2one(
        'stock.warehouse', string="Warehouse",
        domain=[('location_type', '=', 'view')])
    # ('is_parts_warehouse', '!=', True)])
    company_id = fields.Many2one(
        'res.company', 'Company',
        readonly=True, index=True, required=True,
        default=lambda self: self.env.company)
    virtual_location_id = fields.Many2one(
        'stock.location', string="Virtual Location",
        domain="[('scrap_location', '=', True),('company_id', '=', company_id)]")
    transfer_type = fields.Selection(
        [
            ('warehouse_to_warehouse', 'Warehouse to Warehouse'),
            ('warehouse_to_virtual', 'Warehouse to Virtual Location'),
            ('virtual_to_warehouse', 'Virtual Location to Warehouse')],
        required=True, )
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], default='draft')
    transfer_reason = fields.Text(string='Transfer Reason',
                                  help='add transfer reason for the products')

    categ_ids = fields.Many2many(
        'product.category',
        domain="[('id', 'in', dom_category_ids)]")
    dom_category_ids = fields.Many2many(
        'product.category',
        compute='_compute_categ_ids')
    dom_product_ids = fields.Many2many(
        'product.product', compute='_compute_categ_ids')
    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        domain="[('product_type', '=', 'product'), ('id', 'in', dom_product_ids), ('id', 'not in', list_product_ids)]",
        help="Specify Products to focus your inventory on particular Products.")
    list_product_ids = fields.Many2many(
        'product.product', 'list_product_ids_rel', string='Products', check_company=True,
        help="Already added products", compute='_compute_list_product_ids')
    virtual_transfer_lines_ids = fields.One2many(
        'virtual.location.transfer.line', 'virtual_transfer_id')
    picking_id = fields.Many2one('stock.picking')
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id)

    @api.depends('categ_ids', 'product_ids')
    def _compute_categ_ids(self):
        """ to compute product and categories"""
        for rec in self:
            categ = self.env['product.template'].search([
                ('operator_id', '=', rec.company_id.id),
                ('product_type', '=', 'product')
            ]).mapped('categ_id').filtered(lambda c: c.active).ids
            # print('category', categ)
            # print('newcateg',self.env['product.category'].browse(categ))
            rec.dom_category_ids = categ
            # print('categ_rec.', rec.dom_category_ids)
            product_ids = self.env['product.template'].search(
                [('product_type', '=', 'product'), ('operator_id', '=', rec.company_id.id)]).mapped(
                'product_variant_id').ids
            rec.dom_product_ids = product_ids
            # print('product_ids', product_ids)
            if rec.categ_ids:
                product_ids = self.env['product.template'].search(
                    [('categ_id', 'in', rec.categ_ids.ids), ('operator_id', '=', rec.company_id.id),
                     ('product_type', '=', 'product')]).mapped(
                    'product_variant_id').ids
                rec.dom_product_ids = product_ids
            # print(rec.dom_product_ids, "kkkk")

    @api.depends('virtual_transfer_lines_ids')
    def _compute_list_product_ids(self):
        """ to get Transfer line Products"""
        for rec in self:
            rec.list_product_ids = self.virtual_transfer_lines_ids.mapped('product_id').ids
            # print('rec.list_product_ids', rec.list_product_ids)

    def action_start(self):
        """ To Add products to Transfer lines"""
        existing_products = self.virtual_transfer_lines_ids.mapped('product_id')
        if not existing_products:
            self.virtual_transfer_lines_ids = None
            self.ensure_one()
            self.check_and_validate()
            product_pool = self.env['product.product']
            domain = [('operator_id', '=', self.company_id.id),
                      ('active', '=', True), ('product_type', '=', 'product')]
            if self.categ_ids and len(self.categ_ids) > 1:
                domain.append(('categ_id', 'in', tuple(self.categ_ids.ids)))
            elif self.categ_ids:
                domain.append(('categ_id', '=', self.categ_ids.id))
            if self.product_ids and len(self.product_ids) > 1:
                domain.append(('id', 'in', tuple(self.product_ids.ids)))
            elif self.product_ids:
                domain.append(('id', '=', self.product_ids.id))
            wh_products = product_pool.search(domain)
            product_list = []
            for product in wh_products:
                product = product._origin
                cur_wh_stock = self.env['stock.quant'].sudo().search(
                    [('product_id', '=', product.id), (
                        'location_id', 'in',
                        self.warehouse_id.lot_stock_id.ids)],
                    limit=1).quantity
                order_lines = (0, 0, {
                    'product_id': product.id,
                    'product_code': product.default_code,
                    'on_hand_qty': cur_wh_stock,
                    'product_uom_id': product.uom_id.id,
                    'virtual_transfer_id': self.id,
                })
                product_list.append(order_lines)
            self.virtual_transfer_lines_ids = [(2, 0, 0)] + product_list
            self.product_ids = None

    def check_and_validate(self):
        """ Function for checking and validating everything seems correct
            and update sequence name"""
        if not self.sequence:
            ref = self.env.ref(
                'averigo_inventory_operations.wh_transfer_sequence')
            self.sequence = ref.with_company(self.company_id.id).next_by_code(
                "virtual.location.transfer") or _('New')
            self.name = self.sequence

    def action_transfer(self):
        """ Function For Transferring stock"""
        if self.virtual_transfer_lines_ids:
            if sum(self.virtual_transfer_lines_ids.mapped('product_qty')) == 0:
                raise UserError(_("Please add Transfer Quantity to transfer the products."))
            if self.transfer_type == 'warehouse_to_virtual' and self.warehouse_id and self.virtual_location_id:
                name = self.name
                source_location = self.warehouse_id.lot_stock_id.id
                destination_location = self.virtual_location_id.id
                picking_type_id = self.warehouse_id.in_type_id
                line_ids = self.virtual_transfer_lines_ids.filtered(lambda s: s.product_qty > 0)
                move_lines = []
                for line in line_ids:
                    move_line = (0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_qty,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': source_location,
                        'location_dest_id': destination_location,
                        'name': name + " " + line.product_id.name,
                        'state': 'draft',
                    })
                    move_lines.append(move_line)
                vals = {
                    'picking_type_id': picking_type_id.id,
                    'origin': self.name,
                    'location_id': source_location,
                    'location_dest_id': destination_location,
                    'move_ids_without_package': move_lines
                }
                # print('vals', vals)
                picking_id = self.env['stock.picking'].create(vals)
                # print('picking_id', picking_id)
                picking_id.action_assign()
                for move in picking_id.move_ids_without_package:
                    move.quantity = move.product_uom_qty
                picking_id.button_validate()
                self.picking_id = picking_id.id
                self.state = 'done'
            elif self.transfer_type == 'virtual_to_warehouse' and self.virtual_location_id and self.warehouse_id:
                name = self.name
                source_location = self.virtual_location_id.id
                destination_location = self.warehouse_id.lot_stock_id.id
                picking_type_id = self.warehouse_id.in_type_id
                line_ids = self.virtual_transfer_lines_ids.filtered(lambda s: s.product_qty > 0)
                move_lines = []
                for line in line_ids:
                    move_line = (0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_qty,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': source_location,
                        'location_dest_id': destination_location,
                        'name': name + " " + line.product_id.name,
                        'state': 'draft',
                    })
                    move_lines.append(move_line)
                vals = {
                    'picking_type_id': picking_type_id.id,
                    'origin': self.name,
                    'location_id': source_location,
                    'location_dest_id': destination_location,
                    'move_ids_without_package': move_lines
                }
                picking_id = self.env['stock.picking'].create(vals)
                picking_id.action_assign()
                for move in picking_id.move_ids_without_package:
                    move.quantity = move.product_uom_qty
                picking_id.button_validate()
                self.picking_id = picking_id.id
                self.state = 'done'
            elif self.transfer_type == 'warehouse_to_warehouse' and self.warehouse_id and self.warehouse_to_id:
                name = self.name
                source_location = self.warehouse_id.lot_stock_id[0].id
                destination_location = self.warehouse_to_id.lot_stock_id.id
                line_ids = self.virtual_transfer_lines_ids.filtered(lambda s: s.product_qty > 0)
                picking_type_id = self.warehouse_id.in_type_id
                move_lines = []
                for line in line_ids:
                    move_line = (0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_qty,
                        'product_uom': line.product_id.uom_id.id,
                        'location_id': source_location,
                        'location_dest_id': destination_location,
                        'name': name + " " + line.product_id.name,
                        'state': 'draft',
                    })
                    move_lines.append(move_line)
                vals = {
                    'picking_type_id': picking_type_id.id,
                    'origin': self.name,
                    'location_id': source_location,
                    'location_dest_id': destination_location,
                    'move_ids_without_package': move_lines
                }
                picking_id = self.env['stock.picking'].create(vals)
                picking_id.action_assign()
                for move in picking_id.move_ids_without_package:
                    move.quantity = move.product_uom_qty
                picking_id.button_validate()
                self.state = 'done'
                self.picking_id = picking_id.id
                # print('new_picking_id', picking_id)
            else:
                raise UserError(_("Please Add The Warehouse / Virtual Location"))
        else:
            raise UserError(_("Products To Transfer Not Added"))


class VirtualLocationTransferLine(models.Model):
    """Virtual Location Transfer Line"""
    _name = "virtual.location.transfer.line"
    _inherit = ['mail.thread']
    _description = 'Virtual Location Transfer line'

    virtual_transfer_id = fields.Many2one(
        'virtual.location.transfer', 'Virtual Location Transfer', check_company=True,
        index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        index=True, required=True, readonly=True)
    on_hand_qty = fields.Integer(readonly=True)
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        required=True, readonly=True)
    product_qty = fields.Integer(
        'Transfer Quantity',
        digits='Product Unit of Measure')
    categ_id = fields.Many2one(
        related='product_id.categ_id', store=True)
    company_id = fields.Many2one(
        'res.company', 'Company', related='virtual_transfer_id.company_id',
        index=True, readonly=True, store=True)
    product_code = fields.Char(store=True, related='product_id.default_code')

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        """Add validations for Transfer Qty"""
        if not self.virtual_transfer_id.transfer_type == 'virtual_to_warehouse':
            if self.on_hand_qty < 0:
                raise UserError(_("Can't transfer product with -ve Quantity"))

            elif self.product_qty > self.on_hand_qty:
                raise UserError(_("The Transfer Qty should not greater than "
                                  "the On Hand Qty"))
            elif self.product_qty < 0:
                raise UserError(_("The Transfer Qty must be greater than Zero"))
