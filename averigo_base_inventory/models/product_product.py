# -*- coding: utf-8 -*-

from odoo import models, _

class Product(models.Model):
    _inherit = "product.product"
    def action_open_quants(self):
        """override this function to filter the on-hand quantity
                 based on warehouse """
        hide_location = not self.env.user.has_group('stock.group_stock_multi_locations')
        hide_lot = all(product.tracking == 'none' for product in self)
        self = self.with_context(
            hide_location=hide_location, hide_lot=hide_lot,
            no_at_date=True, search_default_on_hand=True,
        )
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
                    self = self.with_context(default_location_id=warehouse.lot_stock_id.id)
        # Set default product id if quants concern only one product
        if len(self) == 1:
            self = self.with_context(
                default_product_id=self.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_ids=self.product_tmpl_id.ids)
        action = self.env['stock.quant'].action_view_quants()
        # note that this action is used by different views w/varying customizations
        if not self.env.context.get('is_stock_report'):
            action['domain'] = [('product_id', 'in', self.ids),
                                ('location_id.warehouse_id.location_type', '=', 'view')]
            action["name"] = _('Update Quantity')
        return action
