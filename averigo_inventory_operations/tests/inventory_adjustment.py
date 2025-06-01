# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from datetime import datetime


class TestInventoryAdjustment(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Inventory = self.env['stock.inventory']
        self.Product = self.env['product.product']
        self.Location = self.env['stock.location']
        self.Warehouse = self.env['stock.warehouse']
        self.Category = self.env['product.category']
        self.UOM = self.env.ref('uom.product_uom_unit')

        # Create test category
        self.test_category = self.Category.create({'name': 'Test Category'})

        # Create test product
        self.product = self.Product.create({
            'name': 'Test Product',
            'default_code': 'TP01',
            'type': 'product',
            'categ_id': self.test_category.id,
            'uom_id': self.UOM.id,
            'uom_po_id': self.UOM.id,
            'standard_price': 10.0
        })

        # Create location
        self.location = self.env['stock.location'].create({
            'name': 'Test Bin',
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'usage': 'internal',
            'is_bin_location': True
        })

        # Get or create warehouse
        self.warehouse = self.Warehouse.search([], limit=1)

        # Create inventory
        self.inventory = self.Inventory.create({
            'name': 'INV/001',
            'warehouse_id': self.warehouse.id,
            'bin_location_ids': [(6, 0, [self.location.id])],
            'product_ids': [(6, 0, [self.product.id])],
            'scan_type': 'product_ids',
            'prefill_counted_quantity': 'zero',
            'state': 'draft',
        })

    def test_01_inventory_creation(self):
        """Test inventory record was created."""
        self.assertTrue(self.inventory, "Inventory not created properly.")
        self.assertEqual(self.inventory.state, 'draft')

    def test_02_start_inventory(self):
        """Test action_start to generate stock lines."""
        self.inventory.action_start()
        self.assertEqual(self.inventory.state, 'confirm')
        self.assertTrue(self.inventory.stock_lines_ids, "Stock lines not created.")

    def test_03_validate_inventory(self):
        """Test validating inventory updates stock."""
        self.inventory.action_start()
        line = self.inventory.stock_lines_ids[0]
        line.write({'product_qty': 5})
        self.inventory.action_validate()
        self.assertEqual(self.inventory.state, 'done')
        quant = self.env['stock.quant'].search([
            ('product_id', '=', self.product.id),
            ('location_id', '=', line.location_id.id)
        ])
        self.assertTrue(quant)
        self.assertEqual(quant.quantity, 5)

    def test_04_prevent_validation_if_not_confirm(self):
        """Should raise error if inventory not in confirm state."""
        with self.assertRaises(UserError):
            self.inventory.action_validate()

    def test_05_deletion_restriction(self):
        """Only non-done inventories should be deletable."""
        self.inventory.action_start()
        self.inventory.action_delete_draft_inventory()
        self.assertFalse(self.Inventory.search([('id', '=', self.inventory.id)]), "Inventory should be deleted.")

    def test_06_negative_qty_error(self):
        """Should raise error for negative quantity."""
        self.inventory.prefill_counted_quantity = 'counted'
        self.inventory.action_start()
        line = self.inventory.stock_lines_ids[0]
        line.write({'product_qty': -5})
        with self.assertRaises(UserError):
            self.inventory.action_validate()
