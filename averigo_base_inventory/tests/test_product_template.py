# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSingleProductMaster(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockLocation = cls.env['stock.location']
        cls.AccountTax = cls.env['account.tax']
        cls.AccountTaxGroup = cls.env['account.tax.group']

        cls.account_tax_group = cls.AccountTaxGroup.create([{
            'name': 'Test Account Tax Group',
            'company_id': cls.env.ref('base.main_company').id,
        }])

        cls.account_tax = cls.AccountTax.create([{
            'name': 'CRV 5 Cents',
            'type_tax_use': 'sale',
            'amount_type': 'fixed',
            'amount': 0.05,
            'active': True,
            'crv': True,
            'description': '5 Cents',
            'tax_group_id': cls.account_tax_group.id,
            'company_id': cls.env.ref('base.main_company').id,
            'country_id': cls.env.ref('base.main_company').country_id.id,
        }])

        cls.company = cls.env['res.company'].create([{
            'name': 'New Test Company',
            'email': 'company.newtest@example.com',
            'country_id': cls.env.ref('base.us').id,
            'currency_id': cls.env.ref('base.USD').id,
        }])
        cls.partner = cls.env['res.partner'].create([{
            'name': 'Test Partner',
            'zip': 90003,
        }])
        cls.user = cls.env['res.users'].create([{
            'name': 'Test User',
            'login': 'test_user',
        }])
        cls.product_category = cls.env['product.category'].create([{
            'name': 'Test Category',
        }])
        cls.uom = cls.env['uom.uom'].create([{
            'name': 'Test UoM',
            'category_id': cls.env.ref('uom.product_uom_categ_unit').id,
            'uom_type': 'bigger',
            'company_id': cls.company.id,
        }])
        cls.warehouse_view = cls.env['stock.warehouse'].create([{
            'name': 'Warehouse View',
            'code': 'WHV',
            'company_id': cls.company.id,
            'location_type': 'view',
        }])
        cls.warehouse_no_view = cls.env['stock.warehouse'].create([{
            'name': 'Warehouse No View',
            'code': 'WHNV',
            'company_id': cls.company.id,
            'location_type': 'pantry',
        }])
        cls.bin_location_view = cls.env['stock.location'].create([{
            'name': 'Bin Location View',
            'is_bin_location': True,
            'company_id': cls.company.id,
            'warehouse_id': cls.warehouse_view.id,
        }])
        cls.bin_location_no_view = cls.env['stock.location'].create([{
            'name': 'Bin Location No View',
            'is_bin_location': True,
            'company_id': cls.company.id,
            'warehouse_id': cls.warehouse_no_view.id,
        }])
        cls.product = cls.env['product.template'].create([{
            'name': 'Test Product',
            'categ_id': cls.product_category.id,
            'type': 'consu',
            'uom_id': cls.uom.id,
            'uom_po_id': cls.uom.id,
        }])

    def test_get_default_uom_id(self):
        """Test that the default UOM (Unit of Measure) is correctly retrieved for the company."""
        uom = self.env['uom.uom'].search([('company_id', '=', self.company.id)],limit=1)
        self.assertTrue(uom.id, msg="Default UOM should be the one with name 'Test uom'")
        _logger.info('test_get_default_uom_id passed')

    def test_compute_product_code_visibility(self):
        """Test the computation of product code visibility based on company settings."""
        self.company.write({
            'enable_item_code': True,
        })
        self.product.write({
            'operator_id': self.company,
        })
        self.product._compute_product_code_visibility()
        self.assertEqual(self.product.enable_product_code, self.product.operator_id.enable_item_code, "Product code visibility was not computed correctly")
        _logger.info('test_compute_product_code_visibility passed')

    def test_valid_check_reorder_point_qty(self):
        """Test that a valid reorder_point and reorder_qty does not raise an error."""
        self.product.reorder_qty = 20
        self.product.reorder_point = 10
        self.assertGreater(self.product.reorder_qty, self.product.reorder_point,
                           msg="Micromarket Min cannot be greater than Micromarket Max.")
        _logger.info('test_valid_check_reorder_point_qty passed')

    def test_invalid_check_reorder_point_qty(self):
        """Test that an invalid reorder_point and reorder_qty raises a ValidationError."""
        with self.assertRaises(ValidationError, msg="Micromarket Min cannot be greater than Micromarket Max."):
            self.product.write({'reorder_qty': 20, 'reorder_point': 30})
        _logger.info('test_invalid_check_reorder_point_qty passed')

    def test_equal_check_reorder_point_qty(self):
        """Test that equal reorder_point and reorder_qty does not raise an error."""
        self.product.reorder_qty = 20
        self.product.reorder_point = 20
        # Save should succeed without raising a ValidationError
        self.assertEqual(self.product.reorder_qty, self.product.reorder_point,
                         msg="Micromarket Min cannot be greater than Micromarket Max.")
        _logger.info('test_equal_check_reorder_point_qty passed')

    def test_compute_list_price(self):
        """Test the computation of the list price based on changes in `list_price_1`."""
        self.product.list_price_1 = 100.0
        self.assertEqual(self.product.list_price, 100.0, "The list_price should be equal to list_price_1 initially.")
        # Change the list_price_1 and check if list_price is updated
        self.product.list_price_1 = 200.0
        self.product._compute_list_price()  # Manually trigger the computation
        self.assertEqual(self.product.list_price, 200.0,
                         "The list_price should update to the new value of list_price_1.")
        _logger.info('test_compute_list_price passed')

    def test_onchange_property_cost_method(self):
        """Test _onchange_property_cost_method updates property_cost_method correctly."""
        # Change to a category with 'fifo' cost method
        self.product_category.write({'property_cost_method': 'fifo'})
        self.product._onchange_property_cost_method()
        self.assertEqual(self.product.property_cost_method, 'fifo',
                         msg="The property_cost_method should be updated to 'fifo' based on the category.")
        # Change to a category with average cost method
        self.product_category.write({'property_cost_method': 'average'})
        self.product._onchange_property_cost_method()
        self.assertEqual(self.product.property_cost_method, 'average',
                         msg="The property_cost_method should be updated to 'average' based on the category.")
        # Change back to a category with 'standard' cost method
        self.product_category.write({'property_cost_method': 'standard'})
        self.product._onchange_property_cost_method()
        self.assertEqual(self.product.property_cost_method, 'standard',
                         msg="The property_cost_method should be updated to 'standard' based on the category.")
        _logger.info('test_onchange_property_cost_method passed')

    def test_default_property_cost_method(self):
        """Test the default cost method for products."""
        result = self.product._default_property_cost_method()
        self.assertEqual(result, 'standard', msg="Default cost method should ")
        # Test product category with a specific cost method
        self.product_category.write({'property_cost_method': 'fifo'})
        self.product = self.product.with_context(default_categ_id=self.product_category.id)
        result = self.product._default_property_cost_method()
        self.assertEqual(result, 'fifo', msg='Cost method should be same as the categories cost method.')
        _logger.info('test_default_property_cost_method passed')

    def test_get_default_product_category_id(self):
        """Test the retrieval of the default product category ID."""
        category = self.product_category.create([{
            'name': 'Default Category',
            'operator_id': self.env.user.company_id.id,
        }])
        result = self.product._get_default_product_category_id()
        self.assertEqual(result, category.id, msg="Default category should be the one with name 'Default Category'")
        self.product_category.search([
            ('company_id', '=', self.env.user.company_id.id),
            ('name', '=', 'Default Category')
        ]).unlink()
        result = self.product._get_default_product_category_id()
        self.assertNotEqual(self.product_category.browse(result).name, 'Default Category')
        _logger.info('test_get_default_product_category_id passed')


    def test_default_get_cost_method(self):
        """Test the default cost method for products based on different contexts."""
        test_cases = [
            ({'categ_id': 1}, 'standard'),  # valid categ_id, expecting 'standard' as default
            ({}, 'standard'),  # no categ_id in context, expecting 'standard'
            ({'categ_id': 9999}, 'standard')  # invalid categ_id, expecting 'standard'
        ]
        for context, expected_value in test_cases:
            # Set the context
            self.env.context = context
            # Call default_get for the 'property_cost_method' field
            defaults = self.env['product.product'].default_get(['property_cost_method'])
            # Check that 'property_cost_method' is in the defaults
            self.assertIn('property_cost_method', defaults)
            # Check that 'property_cost_method' has the expected default value
            self.assertEqual(defaults['property_cost_method'], expected_value)
        _logger.info('test_default_get_cost_method passed')

    def test_compute_primary_locations(self):
        """Test the computation of primary locations for the product."""
        expected_primary_locations = self.env['stock.location'].sudo().search(
            [('is_bin_location', '=', True),
             ('company_id', '=', self.env.company.id)], order='id')
        self.product.compute_primary_locations()
        self.assertEqual(self.product.primary_locations, expected_primary_locations,
                         "Primary locations should only include bin locations with warehouses of type 'view'")
        _logger.info('test_compute_primary_locations passed')


