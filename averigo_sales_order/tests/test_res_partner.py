# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestResPartnerInherit(common.TransactionCase):
    """Customer-Product Association Test Cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.company2 = self.env['res.company'].create([{
            'name': 'Test Company 1',
            'email': 'company.2@test.example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])
        self.ResPartner = self.env['res.partner']
        self.sales_default = self.env['sales.default'].search([('company_id', '=', self.company2.id)])
        self.categ = self.env['product.category'].search([('company_id', '=', self.company2.id)])
        self.uom_categ = self.env['uom.category'].search([('company_id', '=', self.company2.id)])
        self.base_uom = self.env['uom.uom'].search([('company_id', '=', self.company2.id)])
        self.custom_uom_types = self.env['custom.uom.types'].create([{'name': "case"}])
        self.product1 = self.env['product.product'].create([{
            'name': 'Product 1',
            'default_code': 'P1',
            'categ_id': self.categ.id,
            'uom_id':  self.base_uom.id,
            'standard_price': 10.0,
            'list_price': 18.0,
            'list_price_1': 18.0,
            'list_price_2': 17.0,
            'list_price_3': 16.0,
        }])
        self.uom = self.env['multiple.uom'].create([{
            'type': self.custom_uom_types.id,
            'quantity': 10,
            'uom_template_id': self.product1.product_tmpl_id.id,
            'name': 'case (10)',
            'sale_price_1': 25,
        }])
        self.product1.product_uom_ids = [(4, self.uom.id)]
        self.product2 = self.env['product.product'].create([{
            'name': 'Product 2',
            'default_code': 'P2',
            'categ_id':self.categ.id,
            'uom_id': self.base_uom.id,
            'standard_price': 15.0,
            'list_price': 25.0,
            'list_price_1': 25.0,
            'list_price_2': 22.0,
            'list_price_3': 21.0,
        }])
        self.catalog = self.env['product.catalog'].create([{
            'name': 'Test Catalog',
            'catalog_product_ids': [
                (0, 0, {
                    'product_id': self.product1.id,
                    'list_price': 150.0,
                    'uom_id': self.base_uom.id,
                }),
                (0, 0, {
                    'product_id': self.product2.id,
                    'list_price': 250.0,
                    'uom_id': self.base_uom.id,
                }),
            ],
        }])

    def test_add_product(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set the product_ids field with the products created in setUp
        partner.product_ids = self.product1 | self.product2
        # Call the add_product method
        partner.add_product()
        # Check if the products were added correctly
        self.assertEqual(len(partner.customer_product_ids), 2, "Two products should be added to customer_product_ids")
        # Check the details of the first product
        product_line1 = partner.customer_product_ids[0]
        self.assertEqual(product_line1.product_id, self.product1, "The first product should be Product 1")
        self.assertEqual(product_line1.list_price, 18.0, "The list price should be 18.0 for Product 1")
        self.assertEqual(product_line1.margin_price, ((18.0 - 10.0) / 18.0) * 100, "The margin price should be correctly calculated for Product 1")
        # Check the details of the second product
        product_line2 = partner.customer_product_ids[1]
        self.assertEqual(product_line2.product_id, self.product2, "The second product should be Product 2")
        self.assertEqual(product_line2.list_price, 25.0, "The list price should be 23.0 for Product 2")
        self.assertEqual(product_line2.margin_price, ((25.0 - 15.0) / 25.0) * 100, "The margin price should be correctly calculated for Product 2")
        # Check if the product_ids field is cleared after adding products
        self.assertFalse(partner.product_ids, "The product_ids field should be cleared after adding products")

    def test_add_existing_product(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Add a product to customer_product_ids first
        partner.customer_product_ids = [(0, 0, {
            'product_id': self.product1.id,
            'name': self.product1.name,
            'product_code': self.product1.default_code,
            'uom_id': self.product1.uom_id.id,
            'tax_status': self.product1.tax_status,
            'item_cost': self.product1.standard_price,
            'list_price': 18.0,
            'margin_price': ((18.0 - 10.0) / 18.0) * 100,
        })]
        # Set the product_ids field with the same product
        partner.product_ids = self.product1
        # Call the add_product method
        partner.add_product()
        # Check if the product was added to multiple_uom_products
        self.assertEqual(len(partner.multiple_uom_products), 1, "The existing product should be added to multiple_uom_products")
        # Check if the product was not added again to customer_product_ids
        self.assertEqual(len(partner.customer_product_ids), 1, "The existing product should not be added again to customer_product_ids")

    def test_compute_product_select_uom_length(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
            'customer_product_ids':[(0, 0, {
            'product_id': self.product1.id,
            'name': self.product1.name,
            'product_code': self.product1.default_code,
            'uom_id': self.product1.uom_id.id,
            'tax_status': self.product1.tax_status,
            'item_cost': self.product1.standard_price,
            'list_price': 18.0,
            'margin_price': ((18.0 - 10.0) / 18.0) * 100,
        })]
        }])
        # Set the product_ids field with the same product
        partner.product_ids = self.product1
        # Call the add_product method
        partner.add_product()
        # Trigger the compute method
        partner._compute_product_select_uom_length()
        # Check if the computed field is correct
        self.assertEqual(partner.product_select_uom_length, 1, "The computed UoM length should be 1")

    def test_add_multiple_uom_product(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
            'multiple_uom_products': [(0, 0, {
                'product_id': self.product1.id,
                'add_product': True,
                'uom_id': False,
            })]
        }])
        # Test adding a product without UOM
        with self.assertRaises(UserError):
            partner.add_multiple_uom_product()
        # Test adding a product with UOM
        partner.multiple_uom_products.uom_id = self.base_uom.id
        partner.add_multiple_uom_product()
        self.assertTrue(partner.customer_product_ids)

    def test_cancel_multiple_uom_product(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
            'multiple_uom_products': [(0, 0, {
                'product_id': self.product1.id,
                'add_product': True,
                'uom_id': self.base_uom.id,
            })]
        }])
        # Test canceling the multiple UOM product
        partner.add_multiple_uom_product()
        partner.cancel_multiple_uom_product()
        self.assertFalse(partner.multiple_uom_products)
        self.assertFalse(partner.product_ids)

    def test_onchange_catalog_ids(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set catalog_ids
        partner.catalog_ids = self.catalog
        # Call the method
        partner._onchange_catalog_ids()
        # Check if products are added to catalog_product_ids
        self.assertEqual(len(partner.catalog_product_ids), 2)
        self.assertEqual(partner.catalog_product_ids[0].product_id, self.product1)
        self.assertEqual(partner.catalog_product_ids[1].product_id, self.product2)

    def test_add_product_catalog(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set catalog_ids and get products
        partner.catalog_ids = self.catalog
        partner._onchange_catalog_ids()
        # Select all products
        partner.select_catalog_products = True
        partner._onchange_select_all()
        # Call the method
        partner.add_product_catalog()
        # Check if products are added to customer_product_ids
        self.assertEqual(len(partner.customer_product_ids), 2)
        self.assertEqual(partner.customer_product_ids[0].product_id, self.product1)
        self.assertEqual(partner.customer_product_ids[1].product_id, self.product2)

    def test_get_cat_prod_count(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set catalog_ids and get products
        partner.catalog_ids = self.catalog
        partner._onchange_catalog_ids()
        # Call the method
        partner._compute_cat_prod_count()
        # Check if catalog_length is correctly computed
        self.assertEqual(partner.catalog_length, 2)

    def test_select_all(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set catalog_ids and get products
        partner.catalog_ids = self.catalog
        partner._onchange_catalog_ids()
        # Select all products
        partner.select_catalog_products = True
        partner._onchange_select_all()
        # Check if all products are selected
        for catalog_product in partner.catalog_product_ids:
            self.assertTrue(catalog_product.select_product)
        # Deselect all products
        partner.select_catalog_products = False
        partner._onchange_select_all()
        # Check if all products are deselected
        for catalog_product in partner.catalog_product_ids:
            self.assertFalse(catalog_product.select_product)

    def test_reset(self):
        partner = self.ResPartner.create([{
            'name': 'Test Customer1',
            'is_customer': True,
            'zip': '12345',
            'operator_id': self.company2.id,
        }])
        # Set catalog_ids and get products
        partner.catalog_ids = self.catalog
        partner._onchange_catalog_ids()
        # Call the method
        partner.reset()
        # Check if all fields are reset
        self.assertFalse(partner.product_ids)
        self.assertFalse(partner.catalog_ids)
        self.assertFalse(partner.catalog_product_ids)
        self.assertTrue(partner.select_catalog_products)






