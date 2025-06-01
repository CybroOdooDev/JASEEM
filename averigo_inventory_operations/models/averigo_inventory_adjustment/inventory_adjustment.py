# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero


class InventoryAdjustment(models.Model):
    """Class for the model stock_inventory for Inventory Adjustment"""
    _name = 'stock.inventory'
    _inherit = ['mail.thread', "barcodes.barcode_events_mixin"]
    _description = 'Inventory Adjustment'

    name = fields.Char(
        string='Reference No', default="", readonly=True, required=True,
        help="Unique reference number for the inventory record.")
    qty_adjustment = fields.Boolean(
        string='Quantity Adjustment',
        help="Indicates if a quantity adjustment is needed.")
    inventory_date = fields.Datetime(
        string='Inventory date', readonly=True, required=True,
        default=fields.Datetime.now())
    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Warehouse",
        domain=[('location_type', '=', 'view')], readonly=True,
        help="Warehouse location for the inventory.")
    bin_location_ids = fields.Many2many(
        'stock.location', 'bin_location_id',
        string="Bin Locations",
        readonly=True, help="Storage bin locations linked to inventory.",
        domain="[('id', 'in', domain_for_bin_location_ids)]",
        required=True,
    )
    division_id = fields.Many2one(
        'res.division', string="Division", readonly=True,
        help="Company division associated with this inventory.")
    stock_lines_ids = fields.One2many(
        'stock.inventory.line', 'inventory_id',
        string='Stock Lines',
        help="List of stock inventory lines.")
    scan_type = fields.Selection(
        [('product_ids', 'Product'),
         ('product_category_ids', 'Category')],
        string='Scan Type', default='product_ids', required=True,
        help="Choose to scan by product or category.")
    product_category_ids = fields.Many2many(
        'product.category', string='Categories',
        help="Product categories included in this inventory.")
    registered_location_id = fields.Many2one(
        'stock.location', string="Registered Location",
        help="Main stock location for inventory registration.")
    prefill_counted_quantity = fields.Selection(
        [('counted', 'Default to Stock on Hand'),
         ('zero', 'Default to Zero')],
        string='Prefill Counted Quantity', default='counted',
        help="Set initial counted quantity to stock on hand or zero.")
    product_ids = fields.Many2many(
        'product.product', string='Products',
        domain=[('product_type', '=', 'product')],
        help="List of products included in this inventory.")
    add_button = fields.Boolean(
        string='Enable Add Button',
        help="Allows adding products to the inventory manually.")
    state = fields.Selection(
        [('draft', 'Draft'), ('cancel', 'Cancelled'),
         ('confirm', 'In Progress'), ('done', 'Validated')],
        string='Status', default='draft',
        help="Current status of the inventory record.")
    location_ids = fields.Many2many(
        'stock.location', string='Locations',
        readonly=True, check_company=True,
        help="Stock locations covered in this inventory count.")
    company_id = fields.Many2one(
        'res.company', string='Company',
        readonly=True, index=True, required=True,
        default=lambda self: self.env.company,
        help="Company responsible for this inventory.")
    start_empty = fields.Boolean(
        string='Start Empty',
        help="If enabled, starts with an empty inventory.")
    move_ids = fields.One2many(
        'stock.move', 'inventory_id',
        string='Stock Moves',
        help="Stock movements generated from this inventory.")

    domain_for_bin_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_domain_for_bin_location_ids'
    )

    stock_quant_ids = fields.One2many(
        'stock.quantity', 'inventory_id',

    )

    @api.depends('warehouse_id')
    def _compute_domain_for_bin_location_ids(self):
        """Compute bin locations based on warehouse."""
        for rec in self:
            rec.domain_for_bin_location_ids = self.env['stock.location'].search([
                ('warehouse_id', '=', rec.warehouse_id.id)
            ]).ids if rec.warehouse_id else False

    @api.model
    def action_delete_draft_inventory(self):
        """Deletes draft inventories."""
        drafts = self.filtered(lambda inv: inv.state != 'done')
        if not drafts:
            raise UserError(_("Validated entries cannot be deleted."))
        return drafts.unlink()

    @api.onchange('warehouse_id')
    def onchange_bin_loc_ids(self):
        """Clears the bin location IDs when the warehouse changes."""
        self.bin_location_ids = False

    def action_start(self):
        """Initialize stock lines for inventory start."""
        self.stock_lines_ids = [(5, 0, 0)]
        stock_lines = []
        Product = self.env['product.product']
        Quant = self.env['stock.quant']
        Location = self.env['stock.location']

        products = Product.search([('categ_id', 'in', self.product_category_ids.ids)]) \
            if self.scan_type == 'product_category_ids' else self.product_ids

        bin_locations = self.bin_location_ids._origin
        prefill_counted = self.prefill_counted_quantity

        def prepare_line(product, location, on_hand):
            price = product._origin.standard_price
            return (0, 0, {
                'product_code': product.default_code,
                'product_id': product.id,
                'prod_lot_id': False,
                'warehouse_id': self.warehouse_id.id,
                'location_id': location.id,
                'product_uom_qty': product.uom_id.id,
                'standard_price': price,
                'theoretical_qty': on_hand,
                'product_qty': on_hand if prefill_counted == 'counted' else 0,
                'difference_qty': 0 if prefill_counted == 'counted' else -on_hand,
                'current_value': on_hand * price,
                'new_value': on_hand * price if prefill_counted == 'counted' else 0,
                'value_diff': 0 if prefill_counted == 'counted' else -on_hand * price,
                'qty_changed': prefill_counted == 'zero',
            })

        if bin_locations and products:
            for location in bin_locations:
                quants = Quant.search([('location_id', '=', location.id), ('product_id', 'in', products.ids)])
                for product in products:
                    quant = quants.filtered(lambda q: q.product_id == product)
                    on_hand = sum(quant.mapped('inventory_quantity_auto_apply')) or 0
                    stock_lines.append(prepare_line(product, location, on_hand))

        elif bin_locations and not products:
            quants = Quant.search([('location_id', 'in', bin_locations.ids)])
            for quant in quants:
                stock_lines.append(
                    prepare_line(quant.product_id, quant.location_id, quant.inventory_quantity_auto_apply))

        elif self.warehouse_id and not bin_locations and not products:
            locations = Location.search([('warehouse_id', '=', self.warehouse_id.id), ('is_bin_location', '=', True)])
            quants = Quant.search([('location_id', 'in', locations.ids)])
            for quant in quants:
                stock_lines.append(
                    prepare_line(quant.product_id, quant.location_id, quant.inventory_quantity_auto_apply))

        elif products and not bin_locations:
            locations = Location.search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('is_bin_location', '=', True)
            ], limit=1, order='id desc')
            for product in products:
                quants = Quant.search([
                    ('warehouse_id', '=', self.warehouse_id.id),
                    ('product_id', '=', product.id)
                ])
                on_hand = sum(quants.mapped('inventory_quantity_auto_apply')) or 0
                location = quants[0].location_id if quants else locations
                stock_lines.append(prepare_line(product, location, on_hand))

        if stock_lines:
            self.stock_lines_ids = stock_lines
            self.state = 'confirm'

    def action_qty_validate_inventory(self):
        """Validates inventory by updating quantities and creating stock moves."""
        Quant = self.env['stock.quant']
        for line in self.stock_lines_ids.filtered(lambda l: l.qty_changed):
            line.product_id._compute_quantities()
            quant_vals = {
                'warehouse_id': line.warehouse_id.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty.id,
                'location_id': line.location_id.id,
                'quantity': line.product_qty,
                'inventory_quantity': 0,
                'reserved_quantity': 0,
                'inventory_diff_quantity': -line.product_qty,
                'value': line.new_value,
                'on_hand': True,
                'company_id': self.env.company.id,
            }
            quant = Quant.create(quant_vals)
            stock_move_vals = quant._get_inventory_move_values(
                qty=line.product_qty,
                location_dest_id=line.location_id,
                location_id=self.env.ref('stock.stock_location_stock')
            )
            stock_move_vals['reference'] = f'INV {self.name}'
            move = self.env['stock.move'].create(stock_move_vals)
            move.state = 'done'
        self.state = 'done'

    def action_get_product_move(self):
        """View product moves related to current inventory."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_line_action")
        action['domain'] = [('product_id', 'in', self.product_ids.ids)]
        return action

    def action_validate(self):
        """Validates inventory adjustment."""
        self.ensure_one()
        if not self.env.user.has_group('base_averigo.averigo_operator_user_group'):
            raise UserError(_("Only a stock manager can validate an inventory adjustment."))
        if self.state != 'confirm':
            raise UserError(_("Inventory '%s' is either already validated or not ready.") % self.name)

        if not self.stock_lines_ids:
            raise UserError(_("No product selected. Please add a product."))

        quants = self.env['stock.quant'].search([
            ('product_id', 'in', self.stock_lines_ids.mapped('product_id').ids),
            ('warehouse_id', '=', self.warehouse_id.id)
        ])
        for line in self.stock_lines_ids:
            quant = quants.filtered(lambda q: q.product_id == line.product_id)
            if quant:
                quant.write({'quantity': line.product_qty})
            else:
                self.env['stock.quant'].create({
                    'product_id': line.product_id.id,
                    'warehouse_id': self.warehouse_id.id,
                    'location_id': line.location_id.id,
                    'quantity': line.product_qty,
                })
        self._action_done()
        self.stock_lines_ids._check_company()
        self._check_company()
        return True

    def _action_done(self):
        """Finalize inventory and post entries."""
        negative = next((line for line in self.stock_lines_ids if
                         line.product_qty < 0 and line.product_qty != line.theoretical_qty), False)
        if negative:
            raise UserError(
                _('Negative quantity not allowed:\n%s - qty: %s') % (
                    negative.product_id.name, negative.product_qty))

        self.action_check()
        self.move_ids.state = 'done'
        self.write({'state': 'done'})
        self.post_inventory()
        return True

    def post_inventory(self):
        """    Posts the inventory as a single step, moving quants to inventory loss and creating new quants at the specified location."""
        # The inventory is posted as a single step which means quants cannot be moved from an internal location to another using an inventory
        # as they will be moved to inventory loss, and other quants will be created to the encoded quant location. This is a normal behavior
        # as quants cannot be reuse from inventory location (users can still manually move the products before/after the inventory if they want).
        self.mapped('move_ids').filtered(
            lambda move: move.state != 'done')._action_done()
        return True

    def action_check(self):
        """Checks the inventory and computes the stock moves to perform."""
        # tde todo: clean after _generate_moves
        for inventory in self.filtered(
                lambda x: x.state not in ('done', 'cancel')):
            # first remove the existing stock moves linked to this inventory
            inventory.with_context(prefetch_fields=False).mapped(
                'move_ids').unlink()

            inventory.stock_lines_ids._generate_moves()

    def action_cancel_draft(self):
        """Cancels the inventory and resets it to the draft state."""
        self.mapped('move_ids')._action_cancel()
        self.stock_lines_ids.unlink()
        self.write({'state': 'draft'})


class InventoryAdjustmentLine(models.Model):
    """Model representing an inventory adjustment line with various fields and methods for managing inventory adjustments."""
    _name = "stock.inventory.line"
    _inherit = ['mail.thread']
    _description = 'Inventory Adjustment Line'

    warehouse_id = fields.Many2one(
        'stock.warehouse', string="Location",
        domain=[('location_type', '=', 'view')])
    location_id = fields.Many2one(
        'stock.location', string="Bin Location")
    standard_price = fields.Float(
        related='product_id.standard_price')
    current_value = fields.Float(
        compute='compute_value', store=True)
    new_value = fields.Float(
        compute='compute_value', store=True)
    value_diff = fields.Float(
        compute='compute_value', store=True)
    type_id = fields.Many2one(
        comodel_name='adjust.type')
    product_code = fields.Char(
        store=True, related='product_id.default_code')
    item_long_description = fields.Char()
    messages = fields.Char()
    product_id = fields.Many2one(
        'product.product', string='Product')
    inventory_date = fields.Date(
        string='Inventory Date', readonly=True,
        default=lambda self: fields.Datetime.now())
    theoretical_qty = fields.Integer(
        string='On Hand', readonly=True)
    product_qty = fields.Integer(
        string='Counted')
    difference_qty = fields.Integer(
        'Quantity Difference', readonly=True,
        compute='_compute_difference_qty', store=True)
    product_uom_qty = fields.Many2one(
        'uom.uom', 'UoM', readonly=True)
    qty_changed = fields.Boolean()
    state = fields.Selection(
        'Status', related='inventory_id.state')
    inventory_id = fields.Many2one(
        'stock.inventory', 'Inventory', check_company=True,
        index=True, ondelete='cascade')
    prod_lot_id = fields.Many2one(
        'stock.production.lot', 'Lot/Serial Number', check_company=True,
        domain="[('product_id','=',product_id), ('company_id', '=', company_id)]")
    package_id = fields.Many2one(
        'stock.quant.package', 'Pack', index=True, check_company=True,
        domain="[('location_id', '=', location_id)]", )
    partner_id = fields.Many2one(
        'res.partner', 'Owner', check_company=True)
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id',
        index=True, readonly=True, store=True)

    @api.depends('product_qty', 'theoretical_qty')
    def _compute_difference_qty(self):
        """Computes the difference between the counted quantity and the theoretical quantity.
        Also calculates the new value and value difference."""
        for record in self:
            record.difference_qty = record.product_qty - record.theoretical_qty
            record.new_value = record.product_qty * record.standard_price
            record.value_diff = record.new_value - record.current_value
            if record.product_qty != record.theoretical_qty:
                record.qty_changed = True
            else:
                record.qty_changed = False

    @api.depends('theoretical_qty', 'standard_price', 'product_qty')
    def compute_value(self):
        """Computes the current value, new value, and value difference of the inventory line."""
        for rec in self:
            rec.current_value = rec.theoretical_qty * rec.standard_price
            rec.new_value = rec.product_qty * rec.standard_price
            rec.value_diff = rec.new_value - rec.current_value

    def _get_virtual_location(self):
        """Returns the virtual location for inventory adjustments."""
        return self.product_id.with_company(
            self.company_id.id).property_stock_inventory

    def _generate_moves(self):
        """Generates stock moves based on the inventory adjustments."""
        vals_list = []
        for line in self:
            virtual_location = line._get_virtual_location()
            rounding = line.product_id.uom_id.rounding
            if float_is_zero(line.difference_qty, precision_rounding=rounding):
                continue
            if line.difference_qty > 0:  # found more than expected
                vals = line._get_move_values(line.difference_qty,
                                             virtual_location.id,
                                             line.location_id.id, False)
            else:
                vals = line._get_move_values(abs(line.difference_qty),
                                             line.location_id.id,
                                             virtual_location.id, True)
            vals_list.append(vals)
        return self.env['stock.move'].create(vals_list)

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        """Generates the values needed to create a stock move."""
        self.ensure_one()
        return {
            'name': _('INV:') + (self.inventory_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom': self.product_uom_qty.id,
            'product_uom_qty': qty,
            'date': self.inventory_id.inventory_date,
            'company_id': self.inventory_id.company_id.id,
            'inventory_id': self.inventory_id.id,
            'state': 'confirmed',
            'restrict_partner_id': self.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'move_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'date': self.inventory_id.inventory_date,
                'inventory_id': self.inventory_id.id,
                'lot_id': False,
                'product_uom_qty': 0,  # bypass reservation here
                'product_uom_id': self.product_uom_qty.id,
                'qty_done': qty,
                'package_id': out and self.package_id.id or False,
                'result_package_id': (not out) and self.package_id.id or False,
                'location_id': location_id,
                'location_dest_id': location_dest_id,
                'owner_id': self.partner_id.id,
                'quantity': qty,
            })]
        }


class InventoryAdjustmentType(models.Model):
    """Class for the model Inventory Adjustment Type"""
    _name = "adjust.type"
    _description = 'Inventory Adjustment Type'

    name = fields.Char()
    operator_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)


class StockMove(models.Model):
    """Class inherit the model stock_move"""
    _inherit = 'stock.move'

    inventory_id = fields.Many2one(
        'stock.inventory', 'Inventory', check_company=True)


class StockMoveLine(models.Model):
    """Class to inherit the model stock_move_line"""
    _inherit = "stock.move.line"

    user_id = fields.Many2one(
        comodel_name='res.users')
    inventory_id = fields.Many2one(
        comodel_name='stock.inventory')
