# -*- coding: utf-8 -*-
import datetime

import logging
from odoo.exceptions import UserError
from odoo.fields import Datetime
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestSaleOrder(TransactionCase):
    """Sale Order Test Cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.demo_company = self.env['res.company'].sudo().create([{
            'name': 'Demo Company',
            'email': 'demo@example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])
        self.warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.demo_company.id),
             ('location_type', '=', 'view')], limit=1)
        # Create test partners
        self.partner_with_po = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Partner With PO',
            'zip': 90703,
            'po_no': 'TEST123',
        }])
        self.partner_without_po = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Partner Without PO',
            'zip': 90703,
            'po_no': False,
        }])
        self.categ_id = self.env['product.category'].search(
            [('company_id', '=', self.demo_company.id)])
        self.base_uom = self.env['uom.uom'].search(
            [('company_id', '=', self.demo_company.id)])
        self.product = self.env['product.product'].with_company(
            self.demo_company.id).create([{
            'name': 'Physical Product',
            'product_type': 'product',
            'uom_id': self.base_uom.id,
            'list_price_1': 100,
            'categ_id': self.categ_id.id,
        }])
        self.product2 = self.env['product.product'].with_company(
            self.demo_company.id).create([{
            'name': 'Test Product 2',
            'product_type': 'product',
            'uom_id': self.base_uom.id,
            'list_price_1': 100,
            'categ_id': self.categ_id.id,
        }])
        self.service_product = self.env['product.product'].with_company(
            self.demo_company.id).create([{
            'name': 'Service Product',
            'product_type': 'service',
            'list_price_1': 50,
            'list_price_2': 40,
            'categ_id': self.categ_id.id,
        }])
        self.customer = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Partner 1',
            'zip': 90703,
            'is_customer': True,
            'type': 'contact',
            'operator_id': self.demo_company.id,
            'po_no': 'TEST123',
        }])
        self.child_partner = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Child Company',
            'parent_id': self.customer.id,
            'zip': 90703,
            'is_customer': True,
            'type': 'contact',
        }])
        # Create delivery addresses
        self.delivery1 = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Delivery 1',
            'type': 'delivery',
            'zip': 90703,
            'parent_id': self.child_partner.id,
            'street': '123 Main St'
        }])
        self.delivery2 = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Delivery 2',
            'type': 'delivery',
            'parent_id': self.customer.id,
            'zip': 90703,
            'street': '456 Oak Ave'
        }])
        # Create invoice addresses
        self.invoice1 = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Invoice 1',
            'type': 'invoice',
            'zip': 90703,
            'parent_id': self.child_partner.id,
            'street': '789 Finance Blvd'
        }])
        self.invoice2 = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Invoice 2',
            'type': 'invoice',
            'zip': 90703,
            'parent_id': self.customer.id,
            'street': '321 Accounting Ln'
        }])
        # Create test dates
        # Get current datetime and normalize to midnight
        self.today = Datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        self.yesterday = self.today - datetime.timedelta(days=1)
        self.tomorrow = self.today + datetime.timedelta(days=1)
        self.cust_product = self.env['customer.product'].with_company(
            self.demo_company.id).create([{
            'customer_product_id': self.customer.id,
            'product_id': self.product.id,
            'cp_code': 'CP001',
            'uom_id': self.product.uom_id.id,
        }])
        self.custom_uom_types = self.env['custom.uom.types'].with_company(
            self.demo_company.id).create(
            [{'name': "case"}])
        self.uom_2 = self.env['multiple.uom'].with_company(
            self.demo_company.id).create([{
            'type': self.custom_uom_types.id,
            'quantity': 10,
            'uom_template_id': self.product2.product_tmpl_id.id,
            'name': 'case (10)',
            'sale_price_1': 250,
        }])
        self.product2.product_uom_ids = [(4, self.uom_2.id)]

    def test_default_warehouse_id_from_company(self):
        # Set the company's default warehouse ID
        self.demo_company.default_warehouse_id = self.warehouse
        # Call the method
        result = self.env['sale.order'].with_company(
            self.demo_company.id)._default_warehouse_id()
        # Assert the result is the same as the company's default
        self.assertEqual(result, self.warehouse)

    def test_default_warehouse_id_fallback(self):
        # Ensure no default warehouse is set in the company
        self.demo_company.default_warehouse_id = False
        # Call the method
        result = self.env['sale.order'].with_company(
            self.demo_company.id)._default_warehouse_id()
        # Should return a warehouse that matches the fallback search domain
        self.assertTrue(result)
        self.assertEqual(result.location_type, 'view')
        self.assertFalse(result.is_parts_warehouse)

    def test_onchange_partner_with_po(self):
        """Test onchange when partner with PO number is selected"""
        test_record = self.env['sale.order'].new({})
        # Trigger the onchange
        test_record.partner_id = self.partner_with_po
        test_record._onchange_partner_id()
        # Verify the po_no was copied
        self.assertEqual(test_record.po_no, 'TEST123',
                         "PO number should be copied from partner")

    def test_onchange_partner_without_po(self):
        """Test onchange when partner without PO number is selected"""
        test_record = self.env['sale.order'].new({})
        # Trigger the onchange
        test_record.partner_id = self.partner_without_po
        test_record._onchange_partner_id()
        # Verify po_no is False
        self.assertFalse(test_record.po_no,
                         "PO number should be False when partner has no PO")

    def test_onchange_partner_removed(self):
        """Test onchange when partner is removed"""
        test_record = self.env['sale.order'].new({
            'partner_id': self.partner_with_po.id,
            'po_no': 'TEST123'
        })
        # Trigger the onchange by removing the partner
        test_record.partner_id = False
        test_record._onchange_partner_id()
        # Verify po_no was cleared
        self.assertFalse(test_record.po_no,
                         "PO number should be cleared when partner is removed")

    def test_same_date(self):
        """Test when promise date equals order date"""
        test_record = self.env['sale.order'].new({
            'date_order': Datetime.to_string(self.today),
        })
        test_record.promise_date = Datetime.to_string(self.today)
        test_record._onchange_promise_date()
        self.assertEqual(
            test_record.commitment_date,
            self.today,
            "Commitment date should match promise date"
        )

    def test_valid_promise_date(self):
        """Test when promise date is after order date"""
        test_record = self.env['sale.order'].new({
            'date_order': Datetime.to_string(self.today),
        })
        test_record.promise_date = Datetime.to_string(self.tomorrow)
        test_record._onchange_promise_date()
        self.assertEqual(
            test_record.commitment_date,
            self.tomorrow)

    def test_invalid_promise_date(self):
        """Test when promise date is before order date"""
        test_record = self.env['sale.order'].new({
            'date_order': Datetime.to_string(self.today),
        })
        with self.assertRaises(UserError):
            test_record.promise_date = Datetime.to_string(self.yesterday)
            test_record._onchange_promise_date()

    def test_no_service_products(self):
        # Create a sale order with non-service products
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'unit_price': 10,
            })]
        }])
        # Verify computation
        self.assertFalse(order.contain_service_product)

    def test_mixed_products(self):
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'unit_price': 10,
                        'product_uom_qty': 1}),
                (0, 0, {'product_id': self.service_product.id, 'unit_price': 5,
                        'product_uom_qty': 1}),
            ]
        }])
        # Verify computation
        self.assertTrue(order.contain_service_product)

    def test_add_service_product_default_price(self):
        # Create order and add service product
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'service_product_ids': self.service_product,
        }])
        order.add_service_product()
        # Verify line was added correctly
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_id, self.service_product)
        self.assertEqual(order.order_line.unit_price, 50)
        self.assertEqual(order.order_line.product_uom_qty, 0)
        self.assertFalse(order.service_product_ids)

    def test_add_service_product_price_category_2(self):
        # Set partner price category
        self.customer.price_category = 'list_price_2'
        # Create order and add service product
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'service_product_ids': self.service_product,
        }])
        order.add_service_product()
        # Verify correct price was used
        self.assertEqual(order.order_line.unit_price, 40)

    def test_onchange_add_service_product_button(self):
        # Create order
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'service_product_ids': self.service_product,
        }])
        # Trigger onchange
        order.is_add_service_product_button = True
        order._onchange_add_service_product_button()
        # Verify line was added
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line.product_id, self.service_product)

    def test_compute_product_count(self):
        # Create test data
        child_partner = self.env['res.partner'].with_company(
            self.demo_company.id).create([{
            'name': 'Child Partner',
            'zip': 90703,
            'parent_id': self.customer.id
        }])
        # Test with parent partner
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id, }])
        self.assertTrue(order.cus_product_associate)
        # Test with child partner
        child_order = self.env['sale.order'].create(
            [{'partner_id': child_partner.id,
              'company_id': self.demo_company.id}])
        self.assertTrue(child_order.cus_product_associate)
        # Test with partner without products
        empty_partner = self.env['res.partner'].with_company(
            self.demo_company.id).create(
            [{'name': 'Empty Partner',
              'zip': 90703}])
        empty_order = self.env['sale.order'].create(
            [{'partner_id': empty_partner.id,
              'company_id': self.demo_company.id}])
        self.assertFalse(empty_order.cus_product_associate)

    def test_compute_cus_product_filter_ids(self):
        # Test with sell_all_item=True
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'sell_all_item': True,
            'company_id': self.demo_company.id
        }])
        order._compute_cus_product_filter_ids()
        self.assertIn(self.product.id, order.cus_product_filter_ids.ids)
        self.assertIn(self.product2.id, order.cus_product_filter_ids.ids)
        # Test with buy_all_item=True
        self.customer.buy_all_item = True
        order2 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'sell_all_item': False,
            'company_id': self.demo_company.id
        }])
        order2._compute_cus_product_filter_ids()
        self.assertIn(self.product.id, order2.cus_product_filter_ids.ids)
        self.assertIn(self.product2.id, order2.cus_product_filter_ids.ids)
        # Test with regular case (no sell_all_item or buy_all_item)
        self.customer.buy_all_item = False
        order3 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'sell_all_item': False,
            'company_id': self.demo_company.id
        }])
        order3._compute_cus_product_filter_ids()
        self.assertIn(self.product.id, order3.cus_product_filter_ids.ids)
        self.assertNotIn(self.product2.id, order3.cus_product_filter_ids.ids)
        # Test with product already in order line
        order3.order_line.create({
            'order_id': order3.id,
            'product_id': self.product.id,
            'unit_price': 4,
        })
        order3._compute_cus_product_filter_ids()
        self.assertNotIn(self.product.id, order3.cus_product_filter_ids.ids)

    def test_onchange_sell_all_item(self):
        # Test error when no partner is selected
        order = self.env['sale.order'].new({'sell_all_item': True,
                                            'company_id': self.demo_company.id
                                            })
        with self.assertRaises(UserError):
            order._onchange_sell_all_item()
        # Test no error when partner is selected
        order = self.env['sale.order'].new({
            'partner_id': self.customer.id,
            'sell_all_item': True,
            'company_id': self.demo_company.id
        })
        try:
            order._onchange_sell_all_item()
        except UserError:
            self.fail(
                "_onchange_sell_all_item() raised UserError unexpectedly!")
    def test_onchange_associated_product(self):
        # Test error when no partner is selected
        order = self.env['sale.order'].new({'associated_product': True,
                                            'company_id': self.demo_company.id})
        with self.assertRaises(UserError):
            order._onchange_associated_product()

        # Test with partner and associated_product=True
        order = self.env['sale.order'].new({
            'partner_id': self.customer.id,
            'associated_product': True,
            'company_id': self.demo_company.id
        })
        order._onchange_associated_product()
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.order_line[0].product_id, self.product)
        self.assertEqual(order.order_line[0].asso_products, True)

        # Test with associated_product=False
        order.associated_product = False
        order._onchange_associated_product()
        self.assertEqual(len(order.order_line), 0)

    def test_add_products(self):
        # Test with customer product
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        order.cus_product_assoc_ids = self.product
        order.add_products()
        self.assertEqual(len(order.order_line), 1)
        line = order.order_line[0]
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.name, self.cust_product.name)
        self.assertEqual(line.cp_code, self.cust_product.cp_code)
        self.assertEqual(line.unit_price, self.cust_product.list_price)
        order.cus_product_assoc_ids = self.product2
        result = order.add_products()
        self.assertEqual(len(order.order_line), 2)
        line = order.order_line.filtered(lambda l: l.product_id == self.product2)
        self.assertEqual(line.name, self.product2.name)
        self.assertEqual(line.unit_price, self.product2.list_price_1)
        # Verify wizard is returned for non-customer products
        self.assertEqual(result['res_model'], 'product.confirmation')
        # Test _onchange_add_button
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        order.cus_product_assoc_ids = self.product
        order._onchange_add_button()
        self.assertEqual(len(order.order_line), 1)

    def test_compute_partner_shipping_ids(self):
        """Test shipping address computation"""
        # Test with child partner
        order_1 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        order_1.partner_id = self.child_partner
        order_1._compute_partner_shipping_ids()
        self.assertIn(self.delivery1.id,
                      order_1.partner_shipping_ids.ids)
        # Test with parent partner
        order_1.partner_id = self.customer
        order_1._compute_partner_shipping_ids()
        self.assertIn(self.delivery2.id,
                      order_1.partner_shipping_ids.ids)
        # Test with no partner
        order_1.partner_id = False
        order_1._compute_partner_shipping_ids()
        self.assertEqual(len(order_1.partner_shipping_ids), 0)

    def test_compute_partner_invoice_ids(self):
        """Test invoice address computation"""
        # Test with child partner
        order_2 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        order_2.partner_id = self.invoice1.parent_id
        order_2._compute_partner_invoice_ids()
        self.assertIn(self.invoice1.id, order_2.partner_invoice_ids.ids)
        # Test with parent partner
        order_2.partner_id = self.customer
        order_2._compute_partner_invoice_ids()
        self.assertIn(self.invoice2.id, order_2.partner_invoice_ids.ids)
        # Test with no partner
        order_2.partner_id = False
        order_2._compute_partner_invoice_ids()
        self.assertEqual(len(order_2.partner_invoice_ids), 0)

    def test_onchange_partner_shipping_id(self):
        """Test shipping address onchange"""
        order_3 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        # Test with tax_calc > 0
        self.delivery1.tax_calc = 10
        order_3.partner_shipping_id = self.delivery1
        order_3._onchange_partner_shipping_id()

        self.assertEqual(order_3.shp_street, '123 Main St')
        self.assertEqual(order_3.tax_calc, 10)
        self.assertFalse(order_3.tax_rate_is)
        # Test with tax_calc = 0
        self.delivery1.tax_calc = 0
        order_3.partner_shipping_id = self.delivery1
        order_3._onchange_partner_shipping_id()
        self.assertEqual(order_3.tax_calc, 0)
        self.assertTrue(order_3.tax_rate_is)
        # Test with no shipping address
        order_3.partner_shipping_id = False
        order_3._onchange_partner_shipping_id()
        self.assertEqual(order_3.shp_street, '')
        self.assertEqual(order_3.tax_calc, 0)
        self.assertTrue(order_3.tax_rate_is)
    def test_onchange_partner_invoice_id(self):
        """Test invoice address onchange"""
        # Test with invoice address
        order_4 = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        order_4.partner_invoice_id = self.invoice1
        order_4._onchange_partner_invoice_id()
        self.assertEqual(order_4.inv_street, '789 Finance Blvd')
        self.assertEqual(order_4.inv_city, self.invoice1.city)
        # Test with no invoice address
        order_4.partner_invoice_id = False
        order_4._onchange_partner_invoice_id()
        self.assertFalse(order_4.inv_street)
        self.assertFalse(order_4.inv_city)
    def test_compute_total_qty_basic(self):
        # Create a record with order lines
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'order_line': [
                (0, 0, {'product_id': self.product.id, 'unit_price': 4, 'product_uom_qty': 5}),
                (0, 0, {'product_id': self.product2.id, 'unit_price': 5, 'product_uom_qty': 3}),
            ]
        }])
        # Trigger the compute method
        order._compute_total_qty()
        # Verify the total quantity
        self.assertEqual(order.total_qty, 8, "Total quantity should sum to 8")
    def test_compute_total_qty_empty(self):
        # Create a record with no order lines
        order = self.env['sale.order'].create([{
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id
        }])
        # Trigger the compute method
        order._compute_total_qty()
        # Verify the total quantity is 0
        self.assertEqual(order.total_qty, 0,
                         "Total quantity should be 0 for empty order")
    def test_onchange_quantity_basic(self):
        # Create a record with order lines
        order = self.env['sale.order'].new({
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                    'unit_price': 4,
                    'product_uom':self.product.uom_id.id,
                    # Base unit
                }),
                (0, 0, {
                    'product_id': self.product2.id,
                    'product_uom_qty': 3,
                    'unit_price': 5,
                    'product_uom': self.uom_2.convert_uom.id   # Assuming 1 case = 10 units
                }),
            ]
        })
        # Trigger the onchange method
        order._onchange_quantity()
        # Verify the total quantity (3 case = 30 units + 2 units = 32 units)
        self.assertEqual(
            order.total_product_quantity,
            32,
            "Total quantity should account for UoM conversion (30 + 2 = 32)"
        )
    def test_onchange_quantity_empty(self):
        # Create a record with no order lines
        order = self.env['sale.order'].new({
            'partner_id': self.customer.id,
            'company_id': self.demo_company.id,
        })
        # Trigger the onchange method
        order._onchange_quantity()
        # Verify the total quantity is 0
        self.assertEqual(
            order.total_product_quantity,
            0,
            "Total quantity should be 0 for empty order in onchange"
        )


