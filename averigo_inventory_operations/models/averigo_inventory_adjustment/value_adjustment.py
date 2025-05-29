# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG
import logging

_logger = logging.getLogger(__name__)


class ValueInventoryAdjustment(models.Model):
    """Class for the model value_inventory: Value Adjustment"""
    _name = 'value.inventory'
    _inherit = 'mail.thread'
    _description = 'Value Adjustment'

    name = fields.Char(
        'Reference No', default="", readonly=True, required=True)
    date = fields.Datetime(
        'Date', readonly=True, required=True, default=fields.Datetime.now())
    line_ids = fields.One2many(
        'value.inventory.line', 'inventory_id', string='Inventories',
        copy=False, readonly=False)
    company_id = fields.Many2one(
        'res.company', 'Operator', index=True,
        required=True, default=lambda self: self.env.company)
    product_ids = fields.Many2many(
        'product.product', string='Products', check_company=True,
        help="Specify Products to focus your inventory on particular Products.")
    division_id = fields.Many2one(
        'res.division', readonly=True)
    state = fields.Selection(
        string='Status', selection=[
            ('draft', 'Draft'),
            ('cancel', 'Cancelled'),
            ('confirm', 'In Progress'),
            ('done', 'Validated')],
        copy=False, index=True, readonly=True,
        default='draft')

    def action_validate(self):
        """Validates the inventory adjustment by updating the standard cost of products."""
        lines = self.line_ids.filtered(lambda s: s.cost_changed == True)
        if len(lines) == 0:
            raise UserError(_("Nothing to Update"))
        for line in lines:
            line.prv_val = line.current_value
            line.new_val = line.new_value
            line.val_diff = line.value_diff
            change_price_wizard = self.env['stock.change.standard.price'].with_context(
                active_id=line.product_id.product_tmpl_id.id, active_model='product.template').sudo().create(
                {'new_price': line.new_cost, 'date': line.inventory_date})
            change_price_wizard.change_price_update()
        self.state = 'done'

    def action_cancel_draft(self):
        """Cancels the inventory adjustment and sets the state back to 'draft'."""
        self.line_ids.unlink()
        self.write({'state': 'draft'})

    def copy_data(self, default=None):
        """Creates a copy of the inventory adjustment."""
        name = _("%s (copy)") % (self.name)
        default = dict(default or {}, name=name)
        return super().copy_data(default)

    def unlink(self):
        """Deletes an inventory adjustment."""
        for rec in self:
            if (rec.state not in ('draft', 'cancel')
                    and not self.env.context.get(MODULE_UNINSTALL_FLAG, False)):
                raise UserError(_(
                    'You can only delete a draft inventory adjustment. If the inventory adjustment is not done, you can cancel it.'))
        return super(ValueInventoryAdjustment, self).unlink()

    def action_start(self):
        """Starts the inventory adjustment process."""
        self.ensure_one()
        self._action_start()
        return self.action_open_inventory_lines()

    def _action_start(self):
        """Confirms the inventory adjustment."""
        for rec in self:
            if rec.state == 'done':
                continue
            vals = {
                'state': 'confirm',
                'date': fields.Datetime.now()
            }
            rec.line_ids = [(5,0,0)]
            if not rec.line_ids:
                rec.line_ids = self.env['value.inventory.line'].create(rec._get_inventory_lines_values())
            rec.write(vals)

    def action_open_inventory_lines(self):
        """Opens the inventory lines for editing."""
        self.ensure_one()
        action = {}
        context = {'create': False}
        domain = [('inventory_id', '=', self.id)]
        action['context'] = context
        action['domain'] = domain
        return action

    def _get_inventory_lines_values(self):
        """Generates the initial values for inventory lines."""
        lst = []
        if self.product_ids:
            products = self.env['product.product'].search([('id', 'in', self.product_ids.ids)])
        else:
            products = []
        for product in products:
            vals = ({
                'product_id': product.id,
                'inventory_id': self.id,
                'product_uom_id': product.uom_id.id,
                'inventory_date': self.date,
                'prv_cost': product.standard_price,
            })
            lst.append(vals)
        return lst


class ValueInventoryAdjustmentLine(models.Model):
    """Class for the model value_inventory_line : Value Adjustment Line"""
    _name = "value.inventory.line"
    _inherit = 'mail.thread'
    _description = 'Value Adjustment Line'

    inventory_id = fields.Many2one(
        'value.inventory', 'Inventory', check_company=True,
        index=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', 'Product', check_company=True,
        domain="[('type', '=', 'product'), ('company_id', '=', company_id)]",
        index=True, required=True)
    product_code = fields.Char(
        store=True, related='product_id.default_code')
    product_uom_id = fields.Many2one(
        'uom.uom', 'Product Unit of Measure',
        required=True, readonly=True)
    product_qty = fields.Float(
        'Quantity',
        digits='Product Unit of Measure', default=0, compute="compute_product_qty", store=True)
    standard_price = fields.Float(
        related='product_id.standard_price', string='Cost')
    new_cost = fields.Float(
        digits='Product Cost')
    current_value = fields.Float(
        compute='compute_value', digits='Product Cost')
    new_value = fields.Float(
        compute='compute_value', digits='Product Cost')
    value_diff = fields.Float(
        compute='compute_value', digits='Product Cost')
    company_id = fields.Many2one(
        'res.company', 'Company', related='inventory_id.company_id',
        index=True, readonly=True, store=True)
    state = fields.Selection(
        'Status', related='inventory_id.state')
    inventory_date = fields.Datetime(
        'Date', readonly=True, default=fields.Datetime.now,
        help="Last date at which the On Hand Quantity has been computed.")
    cost_changed = fields.Boolean()
    prv_cost = fields.Float(
        digits='Product Cost')
    prv_val = fields.Float(
        digits='Product Cost')
    new_val = fields.Float(
        digits='Product Cost')
    val_diff = fields.Float(
        digits='Product Cost')

    @api.onchange('new_cost')
    def onchange_new_cost(self):
        """Validates the new cost value."""
        if self.new_cost < 0:
            raise UserError(_("New Cost cannot be negative value"))
        if self.new_cost != 0 and self.new_cost != self.standard_price:
            self.cost_changed = True
        else:
            self.cost_changed = False

    @api.depends('new_cost', 'standard_price', 'product_qty', 'cost_changed')
    def compute_value(self):
        """Computes the current and new values, as well as the value difference."""
        for rec in self:
            rec.current_value = rec.product_qty * rec.standard_price
            rec.new_value = rec.product_qty * rec.new_cost
            if rec.cost_changed:
                rec.value_diff = rec.new_value - rec.current_value
            else:
                rec.value_diff = 0

    @api.depends('product_id')
    def compute_product_qty(self):
        """Computes the total product quantity across all warehouses."""
        for rec in self:
            warehouse_ids = self.env['stock.warehouse'].search([('location_type', '=', 'view')])
            quantity = 0
            for warehouse_id in warehouse_ids:
                child_locations = warehouse_id.lot_stock_id.child_ids
                if child_locations:
                    for child_location in child_locations:
                        quant = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id), (
                            'location_id', '=', child_location.id)]).quantity
                        quantity += quant
                parent_quant = self.env['stock.quant'].search([('product_id', '=', rec.product_id.id), (
                    'location_id', 'in', warehouse_id.lot_stock_id.ids)]).quantity
                quantity += parent_quant
            rec.product_qty = quantity


class StockChangeStandardPrice(models.TransientModel):
    """Class for changing the standard price of products and creating accounting moves."""
    _name = "stock.change.standard.price"
    _description = "Stock Change Standard Price"

    date = fields.Date(
        default=fields.Date.context_today)
    new_price = fields.Float(
        'Price', digits='Product Cost', required=True,
        help="If cost price is increased, stock variation account will be debited "
             "and stock output account will be credited with the value = (difference of amount * quantity available).\n"
             "If cost price is decreased, stock variation account will be creadited and stock input account will be debited.")
    counterpart_account_id = fields.Many2one(
        'account.account', string="Counter-Part Account",
        domain=[('deprecated', '=', False)])
    counterpart_account_id_required = fields.Boolean(
        string="Counter-Part Account Required")
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

    @api.constrains('new_price')
    def _check_new_price(self):
        """Validates that the new cost is not negative."""
        if self.new_price and self.new_price < 0:
            raise ValidationError(_("Cost cannot be negative"))

    @api.model
    def default_get(self, fields):
        """Retrieves default values for fields."""
        res = super(StockChangeStandardPrice, self).default_get(fields)
        if 'active_model' in self._context:
            product_or_template = self.env[self._context['active_model']].browse(self._context['active_id'])
            if 'new_price' in fields and 'new_price' not in res:
                res['new_price'] = product_or_template.standard_price
            if 'counterpart_account_id' in fields and 'counterpart_account_id' not in res:
                res[
                    'counterpart_account_id'] = product_or_template.property_account_expense_id.id or product_or_template.categ_id.property_account_expense_categ_id.id
            res['counterpart_account_id_required'] = bool(product_or_template.valuation == 'real_time')
        return res

    def change_price(self):
        """Changes the standard price of products and creates an accounting move."""
        self.ensure_one()
        if self._context['active_model'] == 'product.template':
            products = self.env['product.template'].browse(self._context['active_id']).product_variant_ids
        else:
            products = self.env['product.product'].browse(self._context['active_id'])
        products._change_standard_price(self.new_price, self.date,counterpart_account_id=self.counterpart_account_id.id)
        return {'type': 'ir.actions.act_window_close'}

    def change_price_update(self):
        """Updates the standard price of products and creates an accounting move."""
        self.ensure_one()
        if self._context['active_model'] == 'product.template':
            products = self.env['product.template'].browse(self._context['active_id']).product_variant_id
        else:
            products = self.env['product.product'].browse(self._context['active_id'])
        products._change_standard_price_update(self.new_price, self.date,
                                        counterpart_account_id=self.counterpart_account_id.id)
        return {'type': 'ir.actions.act_window_close'}



class CostChangeTracking(models.Model):
    """Class for the model cost_tracking: Cost Tracking"""
    _name = 'cost.tracking'
    _rec_name = 'product_id'
    _order = 'date'
    _description = 'Cost Tracking'

    user_id = fields.Many2one(
        comodel_name='res.users')
    product_id = fields.Many2one(
        comodel_name='product.template')
    date = fields.Date()
    cost = fields.Float()
    updated_cost = fields.Float()
    operator_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

