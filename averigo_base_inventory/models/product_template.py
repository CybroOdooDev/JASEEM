# -*- coding: utf-8 -*-
from email.policy import default
from unicodedata import category

from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError, RedirectWarning


class UpcChangeHistory(models.Model):
    """Class for the model upc_code_history"""
    _name = "upc.code.history"
    _description = 'UPC Change History'

    note = fields.Char()
    product_id = fields.Many2one(
        'product.template')
    user_id = fields.Many2one(
        comodel_name='res.users', string="User")
    time = fields.Datetime(
        string="Time")


class ProductTemplate(models.Model):
    """class to inherit product_template model"""
    _inherit = 'product.template'

    upc_change_history = fields.One2many(
        'upc.code.history', 'product_id')
    qty_available = fields.Integer(
        'Quantity On Hand', compute='_compute_quantities', search='_search_qty_available',
        compute_sudo=False)

    def _get_default_product_category_id(self):
        category = self.env['product.category'].search(
            [('company_id', '=', self.env.user.company_id.id)], limit=1)
        if category:
            return category.id
        else:
            err_msg = _(
                'You must define at least one product category in order to be able to create products.')
            redir_msg = _('Go to Product Category')
            raise RedirectWarning(err_msg, self.env.ref(
                'product.product_category_action_form').id, redir_msg)



    categ_id = fields.Many2one(
        'product.category', 'Product Category',
        required=True, help="Select category for the current product",
        tracking=True, default=_get_default_product_category_id)
    product_type = fields.Selection(
        [('product', 'Product'), ('service', 'Service')],
        string='Product Type', default='product', required=True)

    @api.onchange('product_type')
    def _onchange_product_type(self):
        """Set type and is_storable based on selected product_type."""
        self.type = 'consu' if self.product_type == 'product' else 'service'
        self.is_storable = (self.product_type == 'product')

    @tools.ormcache()
    def _get_default_uom_id(self):
        return self.env['uom.uom'].sudo().search([('company_id', '=', self.env.user.company_id.id)],limit=1).id

    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.")
    primary_upc = fields.Char(
        string='UPC Code')
    operator_id = fields.Many2one(
        'res.company', 'Operator', required=True, index=True,
        default=lambda self: self.env.company)
    product_code = fields.Char(
        string='Product Code')
    default_code = fields.Char(
        string='Product Code')
    tax_status = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        'Taxable Status', default='yes')
    list_price_1 = fields.Float(
        'List Price 1', digits='Product Price', tracking=True)
    list_price_2 = fields.Float(
        'List Price 2', digits='Product Price', tracking=True)
    list_price_3 = fields.Float(
        'List Price 3', digits='Product Price',tracking=True)
    sale_acc = fields.Many2one(
        'account.account', 'Sales Account', tracking=True)
    vendor = fields.Many2one(
        'res.partner', 'Preferred Vendor')
    cost_price = fields.Float(
        'Price', digits='Product Price')
    cogs_acc = fields.Many2one(
        'account.account', 'COGS Account', tracking=True)
    inventory_acc = fields.Many2one(
        'account.account', 'Inventory Account', tracking=True)
    res_location = fields.Many2one(
        'stock.warehouse', 'Primary Location')

    def _get_primary_location(self):
        bin_locations = self.env['stock.location'].sudo().search(
            [('is_bin_location', '=', True),
             ('company_id', '=', self.env.company.id)], order='id')
        primary_locations = bin_locations.filtered(
            lambda s: s.warehouse_id.location_type == 'view' or not s.warehouse_id)
        for primary_location in primary_locations:
            return primary_location

    primary_location = fields.Many2one(
        'stock.location', 'Primary Location',
        default=_get_primary_location)
    primary_locations = fields.Many2many(
        'stock.location', 'Primary Locations',
        compute='compute_primary_locations')
    res_manufacturer = fields.Many2one(
        'res.partner', 'Manufacturer')
    manufacturer = fields.Text(
        string='Manufacturer')
    product_uom_ids = fields.One2many(
        'multiple.uom', 'uom_template_id',
        string="Add Multiple UoM", copy=True)
    upc_ids = fields.One2many(
        'upc.code.multi', 'upc_id', string="UPC Codes")
    get_barcode = fields.Boolean(
        'get_val', default=False)
    upc_codes = fields.Many2many(
        'upc.code.multi', string='UPCs for Scanning')
    litre_type = fields.Selection(
        [('less_than_750', 'Less than 710 ml'),
         ('greater_710', 'Greater 710 ml')],'Litre Type')
    fluid_ounce = fields.Float(
        'Fluid Ounce', digits='Product Price')
    is_container_tax = fields.Boolean(
        'Container Deposit', default=False)
    mnp_id = fields.Char(
        string='MPN')
    stock_open = fields.Float(
        'Open Stock', digits='Product Unit of Measure')
    reorder_point = fields.Integer(
        'Micromarket Min', default=1)
    reorder_qty = fields.Integer(
        'Micromarket Max', default=1)
    min_qty = fields.Integer(
        'Warehouse Min', default=1)
    max_qty = fields.Integer(
        'Warehouse Max', default=1)
    rate_per_uint = fields.Float(
        'Opening Stock Rate Per Unit', digits='Product Price')
    get_upc_code = fields.Boolean(
        'get_upc_code', default=False)
    is_sugar_tax = fields.Boolean(
        'Sugar Tax', default=False)
    is_container_deposit = fields.Boolean(
        'Deposit Tax', default=False)
    product_image_ids = fields.One2many(
        'extra.image', 'product_tmple_id',
        string="Extra Product Media", copy=True)
    crv_tax = fields.Many2one(
        'account.tax', string='Container Deposit Tax',
        domain="[('crv', '=',  True)]")
    container_deposit_amount = fields.Float(
        'Container Deposit Amount', digits='Product Price')
    legacy = fields.Char(
        string="Legacy System #", help="Number from the legacy system")
    standard_price = fields.Float(
        'Cost', copy=True, inverse='_set_standard_price', search='_search_standard_price',
        digits='Product Price', groups="base.group_system,base_averigo.averigo_operator_user_group",
        help="""In Standard Price & AVCO: value of the product (automatically computed in AVCO).
            In FIFO: value of the last unit that left the stock (automatically computed).
            Used to value the product when the purchase cost is not known (e.g. inventory adjustment).
            Used to compute margins on sale orders.""")
    subsidy_check = fields.Boolean(
        default=False)
    fuel_check = fields.Boolean(
        default=False)
    hazard_check = fields.Boolean(
        default=False)
    enable_product_code = fields.Boolean(
        compute="_compute_product_code_visibility")
    list_price = fields.Float(
        'Sales Price', default=1.0, digits='Product Price',
        compute='_compute_list_price', store=True, readonly=False,
        help="Price at which the product is sold to customers.")
    is_storable = fields.Boolean(
        'Track Inventory', store=True, compute='compute_is_storable',
        readonly=False,
        default=True, precompute=True,
        help='A storable product is a product for which you manage stock.')
    qty = fields.Integer(
        string='On Hand Quantity', compute='_compute_on_hand_quantity')
    transit_qty = fields.Integer(
        string='Transit Quantity', compute='_compute_on_hand_quantity')
    
    @api.constrains('operator_id')
    def _check_operator_id(self):
        """company id and operator id """
        self.company_id = self.operator_id

    @api.depends('company_id', 'enable_product_code')
    def _compute_product_code_visibility(self):
        """Function to compute product code visibility"""
        for rec in self:
            rec.enable_product_code = True if rec.operator_id.enable_item_code else False

    @api.constrains('reorder_point', 'reorder_qty')
    def _check_reorder_point_qty(self):
        """Method is used to ensure that the reorder point is not greater than the reorder quantity."""
        for record in self:
            if record.reorder_point > record.reorder_qty:
                raise ValidationError("Micromarket Min cannot be greater than Micromarket Max.")

    @api.depends('qty', 'transit_qty')
    def _compute_on_hand_quantity(self):
        """this function used to compute the forecasted quantity on smart tab"""
        for rec in self:
            products = []
            rec.qty = 0
            rec.transit_qty = 0
            for product in self.env['product.product'].sudo().search(
                    [('product_tmpl_id', '=', rec.id)]):
                products.append(product.id)
            qty = self.env['stock.quant'].sudo().search([
                ('product_id', 'in', products),
                ('location_id.warehouse_id.location_type', '=', 'view'),
                ('location_id.usage', '=', 'internal')])
            transit_qty = self.env['stock.quant'].sudo().search([
                ('product_id', 'in', products),
                ('location_id.warehouse_id.location_type', '=', 'transit'),
                ('location_id.usage', '=', 'internal')])
            if qty:
                rec.qty += sum(qty.mapped('inventory_quantity'))
            if transit_qty:
                rec.transit_qty += sum(transit_qty.mapped('inventory_quantity'))

    def action_open_truck_quants(self):
        """ this function to filter the on-hand quantity
         based on truck """
        product = self.env['product.product'].sudo().search([
            ('product_tmpl_id', '=', self.id)])
        domain = [('product_id', 'in', product.ids),
                  ('location_id.warehouse_id.location_type', '=', 'transit')]
        hide_location = not self.env.user.has_group(
            'stock.group_stock_multi_locations')
        hide_lot = all([product.tracking == 'none' for product in self])
        self = self.with_context(hide_location=hide_location, hide_lot=hide_lot)
        # If user have rights to write on quant, we define the view as editable.
        if self.env.user.has_group('stock.group_stock_manager'):
            self = self.with_context(inventory_mode=True)
            # Set default location id if multilocations is inactive
            if not self.env.user.has_group('stock.group_stock_multi_locations'):
                user_company = self.env.company
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', user_company.id)], limit=1
                )
                if warehouse:
                    self = self.with_context(
                        default_location_id=warehouse.lot_stock_id.id)
        # Set default product id if quants concern only one product
        if len(self) == 1:
            self = self.with_context(
                default_product_id=product.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_ids=self.product_tmpl_id.ids)
        ctx = dict(self.env.context)
        ctx.update({'no_at_date': True})
        return self.env['product.template'].with_context(
            ctx)._get_truck_quants_action(
            domain)

    @api.model
    def _get_truck_quants_action(self, domain=None, extend=False):
        """ Returns an action to open quant view.
        Depending of the context (user have right to be inventory mode or not),
        the list view will be editable or readonly.

        :param domain: List for the domain, empty by default.
        :param extend: If True, enables form, graph and pivot views. False by default.
        """
        if not self.env['ir.config_parameter'].sudo().get_param(
                'stock.skip_quant_tasks'):
            self.env['stock.quant']._quant_tasks()
        ctx = dict(self.env.context or {})
        ctx.pop('group_by', None)
        action = {'name': _('Truck Quantity'), 'view_type': 'list',
                  'view_mode': 'list', 'res_model': 'stock.quant',
                  'type': 'ir.actions.act_window', 'context': ctx,
                  'domain': domain or [], 'view_id': self.env.ref(
                'averigo_base_inventory.stock_truck_quant_tree').id}
        # fixme: erase the following condition when it'll be possible to create a new record
        return action

    def action_view_averigo_stock_move_lines(self):
        """This function only shows the warehouse stock moves."""
        # Get the action reference
        action = self.env.ref('stock.stock_move_line_action').read()[0]
        # Search for the move lines based on specified criteria
        move_lines = self.env['stock.move.line'].search([
            ('product_id.product_tmpl_id', 'in', self.ids)
        ])
        line = move_lines.filtered(
            lambda l: not (
                    l.location_id.warehouse_id.location_type == 'micro_market' and
                    l.location_dest_id.usage == 'customer')).mapped('id')
        action['domain'] = [('id', 'in', line)]
        # Ensure the view mode includes 'tree' to display the tree view
        action['view_mode'] = 'list,form'
        action['path'] = 'moves-history'
        # Remove groupby settings from the context
        if 'context' in action:
            context = eval(action['context']) if isinstance(action['context'],
                                                            str) else action[
                'context']
            context.pop('search_default_groupby_product_id', None)
            context.pop('search_default_done', None)
            action['context'] = context
        return action

    @api.depends('list_price_1')
    def _compute_list_price(self):
        """Compute method to automatically set the value of `list_price` based on the value of `list_price_1"""
        for record in self:
            record.list_price = record.list_price_1

    @api.onchange('list_price_1')
    def _onchange_list_price(self):
        if self.list_price_1 < 0:
            self.list_price_1 = 0.0
            return {
                'warning': {
                    'title': _("Invalid Price"),
                    'message': _(
                        "Sales price cannot be negative. It has been reset to 0."),
                }
            }
        return None

    @api.onchange('categ_id')
    def _onchange_property_cost_method(self):
        """Function for setting property cost method based on changing the value"""
        for record in self:
            record.property_cost_method = record.categ_id.property_cost_method or 'standard'

    @api.model
    def _default_property_cost_method(self):
        """Function for setting default property cost method"""
        product_category = self.env['product.category'].browse(
            self._context.get('default_categ_id'))
        if product_category:
            return product_category.property_cost_method
        return 'standard'

    @api.model
    def default_get(self, fields):
        """Function for getting default cost method"""
        defaults = super().default_get(fields)
        if 'property_cost_method' in fields and 'categ_id' in self.env.context:
            defaults[
                'property_cost_method'] = self._default_property_cost_method()
        return defaults

    property_cost_method = fields.Selection(
        [('standard', 'Standard Price'), ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string="Costing Method",
        company_dependent=True, copy=True, default=_default_property_cost_method,
        help="""Standard Price: The products are valued at their standard cost defined on the product.
                Average Cost (AVCO): The products are valued at weighted average cost.
                First In First Out (FIFO): The products are valued supposing those that enter the company 
                first will also leave it first.""")
    current_cost = fields.Float(
        string="Last Purchase Cost",readonly=True)

    @api.depends('name')
    def compute_primary_locations(self):
        """Function for computing the primary location"""
        bin_locations = self.env['stock.location'].sudo().search(
            [('is_bin_location', '=', True),
             ('company_id', '=', self.env.company.id)], order='id')
        primary_locations = bin_locations.filtered(
            lambda
                s: s.warehouse_id.location_type == 'view' or not s.warehouse_id)
        self.primary_locations = primary_locations.ids


    @api.model_create_multi
    def create(self, vals_list):
        """Adding product code if the code is not entered manually"""
        for vals in vals_list:
            if not vals.get('default_code'):
                sequence = self.env.ref('averigo_base_inventory.seq_product_code')
                vals['default_code'] = sequence.with_company(
                    self.operator_id.id).next_by_code(
                    'product.code.sequence') or '/'
        res = super().create(vals_list)
        return res


class Barcode(models.Model):
    """Class for the model barcode_barcode."""
    _name = "barcode.barcode"
    _description = 'Temporary, to keep multiple UPC While creating bulk product list from GPM'
    _rec_name = 'barcode'

    barcode = fields.Char(
        string='UPC')
    get_barcode = fields.Boolean(
        'get_val', default=False)
    upc_id = fields.Many2one(
        comodel_name='create.products')


class UPCCode(models.Model):
    """Class for the model upc_code_multi"""
    _name = "upc.code.multi"
    _description = 'Multiple UPC Code in Operator level'
    _rec_name = 'upc_code_id'

    upc_code_id = fields.Char(
        string='UPC Code')
    get_upc_code = fields.Boolean(
        'get_val', default=False)
    upc_id = fields.Many2one(
        comodel_name='product.template')
    product_company_id = fields.Many2one(
        related='upc_id.company_id')
    company_id = fields.Many2one(
        'res.company', 'Operator', required=True,
        default=lambda self: self.env.company)
    _sql_constraints = [
        ('upc_operator_uniq', 'unique(operator_id, upc_code_id)',
         'UPC Code already used by other product!'),
    ]


class ExtraImages(models.Model):
    """Class for the model extra_image"""
    _name = "extra.image"
    _description = 'Multiple images of Product in Operator level'
    _order = 'sequence, id'
    _inherit = ['image.mixin']

    name = fields.Char(
        "Name", required=True)
    image_1920 = fields.Image(
        "Image", required=True)
    product_tmple_id = fields.Many2one(
        'product.template', "Product Template",
        index=True, ondelete='cascade')
    sequence = fields.Integer(
        default=10, index=True)

class CustomerProduct(models.Model):
    """Product Linked/Associated to Customer"""
    _name = "customer.product"
    _inherit = ['mail.thread']
    _description = 'Customer Product'

    customer_product_id = fields.Many2one('res.partner')
    active = fields.Boolean('Active', related='customer_product_id.active')
    product_id = fields.Many2one('product.product', index=True, required=True,
                                 domain="[('type', 'in', ['consu'])]")
    product_code = fields.Char('Product code', store=True,
                               related='product_id.default_code')


