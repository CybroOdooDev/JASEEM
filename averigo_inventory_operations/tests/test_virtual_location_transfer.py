# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo import _
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestVirtualLocation(TransactionCase):

    def setUp(self):
        super(TestVirtualLocation, self).setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
            'email': 'test@example.com' , # Ensure email is provided
            'operator_domain': 'testcompany.com',
            'country_id': self.env.ref('base.us').id
        })

        self.warehouse_1 = self.env['stock.warehouse'].create({
            'name': 'Warehouse 1',
            'code': 'WH1',
            'company_id': self.company.id,
        })
        self.location_1 = self.warehouse_1.lot_stock_id

        self.warehouse_2 = self.env['stock.warehouse'].create({
            'name': 'Warehouse 2',
            'code': 'WH2',
            'company_id': self.company.id,
        })

        self.location_2 = self.warehouse_2.lot_stock_id

        self.category_1 = self.env['product.category'].create({'name': 'Category 1', 'active': True})
        self.category_2 = self.env['product.category'].create({'name': 'Category 2', 'active': True})


        self.product_1 = self.env['product.product'].create({
            'name': 'Product 1',
            'categ_id': self.category_1.id,
            'operator_id': self.company.id,
            'is_storable': True,
        })

        self.product_2 = self.env['product.product'].create({
            'name': 'Product 2',
            'categ_id': self.category_2.id,
            'operator_id': self.company.id,
            'is_storable': True,
        })

        self.env['stock.quant'].create({
            'product_id': self.product_1.id,
            'location_id': self.location_1.id,
            'quantity': 50,  # Initial stock
        })

        self.env['stock.quant'].create({
            'product_id': self.product_2.id,
            'location_id': self.location_1.id,
            'quantity': 100,  # Initial stock
        })

        self.virtual_transfer = self.env['virtual.location.transfer'].create({
            'company_id': self.company.id,
            'warehouse_id': self.warehouse_1.id,
            'warehouse_to_id': self.warehouse_2.id,
            'transfer_type': 'warehouse_to_warehouse',
        })

        self.transfer_line_1 = self.env['virtual.location.transfer.line'].create({
            'virtual_transfer_id': self.virtual_transfer.id,
            'product_id': self.product_1.id,
            'product_uom_id': self.product_1.uom_id.id,
        })
        self.transfer_line_2 = self.env['virtual.location.transfer.line'].create({
            'virtual_transfer_id': self.virtual_transfer.id,
            'product_id': self.product_2.id,
            'product_uom_id': self.product_2.uom_id.id,
        })


    def test_compute_categ_ids(self):
        self.virtual_transfer._compute_categ_ids()
        expected_category_ids = [self.category_1.id, self.category_2.id]
        expected_product_ids = [self.product_1.product_variant_id.id, self.product_2.product_variant_id.id]
        self.assertEqual(set(self.virtual_transfer.dom_category_ids.ids), set(expected_category_ids),
                         "Computed category IDs do not match expected IDs.")
        self.assertEqual(set(self.virtual_transfer.dom_product_ids.ids), set(expected_product_ids),
                         "Computed product IDs do not match expected IDs.")

    def test_compute_categ_ids_with_empty_categories(self):
        """Test when categ_ids is explicitly set to empty"""
        self.virtual_transfer.categ_ids = [(6, 0, [])]  # Empty many2many field
        self.virtual_transfer._compute_categ_ids()
        expected_product_ids = [self.product_1.product_variant_id.id, self.product_2.product_variant_id.id]
        self.assertEqual(set(self.virtual_transfer.dom_product_ids.ids), set(expected_product_ids),
                         "Computed product IDs should match all products when category is empty.")

    def test_compute_list_product_ids(self):
        """Test the _compute_list_product_ids method"""

        # Compute the product list
        self.virtual_transfer._compute_list_product_ids()

        # Expected product IDs
        expected_product_ids = {self.product_1.id, self.product_2.id}

        # Check if computed list_product_ids matches expected products
        self.assertEqual(set(self.virtual_transfer.list_product_ids.ids), expected_product_ids,
                         "Computed list_product_ids do not match expected product IDs.")

    def test_action_start(self):
        """Test the action_start method"""

        # ✅ Ensure transfer lines are empty before calling action_start()
        self.virtual_transfer.virtual_transfer_lines_ids.unlink()

        # Assert that transfer lines are empty
        self.assertFalse(self.virtual_transfer.virtual_transfer_lines_ids,
                         "Transfer lines should be empty before action_start.")

        # Run `action_start()` method
        self.virtual_transfer.action_start()

        # Ensure transfer lines are created
        self.assertTrue(self.virtual_transfer.virtual_transfer_lines_ids,
                        "Transfer lines should be created after action_start.")

        # Get product IDs from transfer lines
        transfer_product_ids = self.virtual_transfer.virtual_transfer_lines_ids.mapped('product_id').ids

        # Expected products to be transferred
        expected_product_ids = [self.product_1.id, self.product_2.id]

        # Check if expected products exist in transfer lines
        self.assertEqual(set(transfer_product_ids), set(expected_product_ids),
                         "Transfer lines should contain the correct products.")

        # ✅ Fix: Use `self.warehouse_1.lot_stock_id.id` instead of `self.warehouse.lot_stock_id.id`
        for line in self.virtual_transfer.virtual_transfer_lines_ids:
            stock = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', self.warehouse_1.lot_stock_id.id)  # ✅ Fixed
            ], limit=1)
            self.assertEqual(line.on_hand_qty, stock.quantity, "On-hand quantity should match stock.")

    def test_check_and_validate(self):
        """Test the check_and_validate method"""

        # Ensure sequence is initially empty
        self.assertFalse(self.virtual_transfer.sequence, "Sequence should be empty before validation.")

        # Run the check_and_validate() method
        self.virtual_transfer.check_and_validate()

        # Ensure sequence is now assigned
        self.assertTrue(self.virtual_transfer.sequence, "Sequence should be generated after validation.")

        # Ensure name is also updated
        self.assertEqual(self.virtual_transfer.name, self.virtual_transfer.sequence,
                         "Name should be updated to the generated sequence.")

    def test_action_transfer_warehouse_to_warehouse(self):
        """Test `action_transfer()` for `warehouse_to_warehouse` transfers"""

        # ✅ Create a warehouse-to-warehouse transfer
        transfer = self.env['virtual.location.transfer'].create({
            'company_id': self.company.id,
            'warehouse_id': self.warehouse_1.id,
            'warehouse_to_id': self.warehouse_2.id,
            'transfer_type': 'warehouse_to_warehouse',
        })

        # ✅ Create transfer lines
        self.env['virtual.location.transfer.line'].create({
            'virtual_transfer_id': transfer.id,
            'product_id': self.product_1.id,
            'product_qty': 10,  # Ensure quantity is > 0
            'product_uom_id': self.product_1.uom_id.id,
        })

        # ✅ Run the transfer
        transfer.action_transfer()

        # ✅ Assertions
        self.assertEqual(transfer.state, 'done', "Transfer should be marked as 'done'.")
        self.assertTrue(transfer.picking_id, "Picking should be created for transfer.")
        self.assertEqual(transfer.picking_id.state, 'done', "Stock picking should be validated.")

    #     super().setUp()
    #     self.company = self.env.company
    #     self.warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company.id)], limit=1)
    #     self.virtual_location = self.env['stock.location'].search(
    #         [('scrap_location', '=', True), ('company_id', '=', self.company.id)])
    #     category = self.env['product.template'].search([
    #         ('operator_id', '=', self.company.id), ('product_type', '=', 'product')]).mapped('categ_id').ids
    #     self.category_ids = self.env['product.category'].browse(category).filtered(lambda c: c.active).ids
    #     product_ids = self.env['product.template'].search(
    #         [('product_type', '=', 'product'), ('operator_id', '=', self.company.id)]).mapped(
    #         'product_variant_id').ids
    #     self.product_ids = self.env['product.product'].browse(product_ids)
    #
    # # Compute domain category IDs based on company's product templates
    # def test_compute_domain_category_ids(self):
    #     record = self.env['virtual.location.transfer'].create({
    #         'company_id': self.company.id,
    #         'transfer_type': 'warehouse_to_warehouse',
    #     })
    #     record._compute_categ_ids()
    #     self.assertEqual(record.dom_category_ids.ids, self.category_ids)
    #
    #     record_emp_categ = self.env['virtual.location.transfer'].create({
    #         'transfer_type': 'warehouse_to_warehouse',
    #         'company_id': self.company.id,
    #         'categ_ids': [(6, 0, [])]  # Empty many2many
    #     })
    #     record_emp_categ._compute_categ_ids()
    #     self.assertEqual(record.dom_product_ids.ids, self.product_ids)
    # def test_empty_sequence_generates_new_sequence(self):
    #     # When sequence is empty, generate new sequence using company reference
    #     transfer = self.env['virtual.location.transfer'].create({
    #         'company_id': self.company.id,
    #         'transfer_type': 'warehouse_to_warehouse',
    #         'sequence': False
    #     })
    #     transfer.check_and_validate()
    #     self.assertNotEqual(transfer.sequence, False)
    #     self.assertEqual(transfer.sequence, transfer.name)
    #
    # def test_add_products_to_empty_transfer_lines(self):
    #     # Adding products to transfer lines when no existing products
    #     transfer = self.env['virtual.location.transfer'].create({
    #         'warehouse_id': self.warehouse.id,
    #         'company_id': self.company.id,
    #         'transfer_type': 'warehouse_to_warehouse',
    #         'virtual_transfer_lines_ids': []
    #     })
    #     categ_id = self.env['product.category'].create({
    #         'name': 'Test Category',
    #         'operator_id': self.company.id
    #     })
    #     product = self.env['product.product'].create({
    #         'name': 'Test Product',
    #         'product_type': 'product',
    #         'operator_id': self.company.id,
    #         'categ_id': categ_id.id,
    #     })
    #     transfer.product_ids = product
    #     transfer.action_start()
    #     self.assertEqual(len(transfer.virtual_transfer_lines_ids), 1)
    #     self.assertEqual(transfer.virtual_transfer_lines_ids[0].product_id.id, product.id)
    #
    # def test_action_start_empty_category_ids(self):
    #     # Handling empty category_ids
    #     VirtualLocationTransfer = self.env['virtual.location.transfer']
    #     transfer = VirtualLocationTransfer.create({
    #         'company_id': self.company.id,
    #         'warehouse_id': self.warehouse.id,
    #         'transfer_type': 'warehouse_to_warehouse',
    #         'categ_ids': False,
    #         'virtual_transfer_lines_ids': []
    #     })
    #     transfer.action_start()
    #     domain = [('operator_id', '=', transfer.company_id.id),
    #               ('active', '=', True),
    #               ('product_type', '=', 'product')]
    #     products = self.env['product.product'].search(domain)
    #     self.assertEqual(len(transfer.virtual_transfer_lines_ids), len(products))
    #
    # def test_empty_transfer_lines(self):
    #     # Handle empty virtual_transfer_lines_ids
    #     virtual_transfer = self.env['virtual.location.transfer'].create({
    #         'name': 'TEST/002',
    #         'transfer_type': 'warehouse_to_virtual',
    #         'warehouse_id': self.warehouse.id,
    #         'virtual_location_id': self.virtual_location.id,
    #         'virtual_transfer_lines_ids': []
    #     })
    #     with self.assertRaises(UserError) as context:
    #         virtual_transfer.action_transfer()
    #
    #     self.assertEqual(str(context.exception), "Products To Transfer Not Added")
