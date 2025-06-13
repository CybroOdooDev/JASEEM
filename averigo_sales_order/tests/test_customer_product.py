# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestCustomerProduct(TransactionCase):
    """Customer Product test cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.company = self.env['res.company'].create([{
            'name': 'Test Company Demo',
            'email': 'company@test.example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])
        self.customer = self.env['res.partner'].create([{
            'name': 'Test Customer',
            'zip':'12345',
            'operator_id': self.company.id,
        }])
        self.categ = self.env['product.category'].search([('company_id', '=', self.company.id)])
        self.uom_categ = self.env['uom.category'].search(
            [('company_id', '=', self.company.id)])
        self.uom = self.env['uom.uom'].search(
            [('company_id', '=', self.company.id)])
        self.product = self.env['product.product'].create([{
            'name': 'Product 1',
            'default_code': 'P1',
            'categ_id': self.categ.id,
            'uom_id': self.uom.id,
            'standard_price': 100.0,
            'list_price': 150.0,
            'list_price_1': 150.0,
            'list_price_2': 17.0,
            'list_price_3': 16.0,
        }])
        self.custom_uom = self.env['custom.uom.types'].create([{'name': 'Box'}])
        self.multiple_uom = self.env['multiple.uom'].create([{
            'uom_template_id': self.product.product_tmpl_id.id,
            'name': 'Product 1',
            'type': self.custom_uom.id,
            'quantity':2,
            'convert_uom': self.uom.id,
            'sale_price_1': 200.0,
            'sale_price_2': 250.0,
            'sale_price_3': 300.0,
        }])
        self.customer_product = self.env['customer.product'].create([{
            'customer_product_id': self.customer.id,
            'product_id': self.product.id,
            'uom_id': self.uom.id,
        }])
        self.catalog = self.env['product.catalog'].create([{
            'name': 'Test Catalog',
            'catalog_product_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'list_price': 150.0,
                    'uom_id': self.uom.id,
                }),
            ],
        }])
    def test_onchange_cp_code(self):
        """ Test _onchange_cp_code method """
        self.customer_product.cp_code = 'Test@Code'
        with self.assertRaises(UserError):
            self.customer_product._onchange_cp_code()
        self.customer_product.cp_code = 'TestCode'
        self.customer_product._onchange_cp_code()
        self.assertEqual(self.customer_product.cp_code, 'TestCode')

    def test_compute_item_cost(self):
        """ Test _compute_item_cost method """
        self.customer_product._compute_item_cost()
        self.assertEqual(self.customer_product.item_cost, 100.0)

    def test_compute_price_status(self):
        """ Test _compute_price_status method """
        self.customer_product.write({'product_id': self.product.id,
            'list_price': 150.0,
            'catalog_id': self.catalog.id,
            'catalog_price': 150.0,})

        self.customer_product._compute_price_status()
        self.assertEqual(self.customer_product.price_status, 'Catalog - Test Catalog')
        self.assertEqual(self.customer_product.margin_price, 33.33333333333333)  # (150 - 200) / 150 * 100
        self.customer_product.list_price = 250.0
        self.customer_product._compute_price_status()
        self.assertEqual(self.customer_product.price_status, 'Entered')
        self.assertEqual(self.customer_product.margin_price, 60.0)
    def test_compute_multiple_uom_id(self):
        """ Test _compute_multiple_uom_id method """
        self.customer_product._compute_multiple_uom_id()
        self.assertIn(self.uom.id, self.customer_product.uom_ids.ids)

    def test_compute_unit_ids(self):
        """ Test _compute_unit_ids method """
        self.customer_product._compute_unit_ids()
        self.assertNotIn(self.uom.id, self.customer_product.unit_ids.ids)

    def test_onchange_list_price(self):
        """ Test _onchange_margin_price method """
        self.customer_product.list_price = 150.0
        self.customer_product._onchange_list_price()
        self.assertEqual(self.customer_product.price_status, 'Entered')
        self.assertEqual(self.customer_product.margin_price, 33.33333333333333)  # (150 - 100) / 150 * 100

        self.customer_product.list_price = 300.0
        self.customer_product._onchange_list_price()
        self.assertEqual(self.customer_product.price_status, 'Entered')
        self.assertEqual(self.customer_product.margin_price, 66.66666666666666)  # (300 - 100) / 300 * 100

    def test_get_uom_id(self):
        """ Test get_uom_id method """
        self.customer_product.uom_id = self.uom.id
        self.customer_product.get_uom_id()
        self.assertEqual(self.customer_product.item_cost, 100.0)
        self.assertEqual(self.customer_product.list_price, 150.0)  # Based on list_price_1