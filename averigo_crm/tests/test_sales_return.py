# -*- coding: utf-8 -*-
from datetime import date

import logging

from odoo import fields
from odoo.exceptions import ValidationError, UserError
from odoo.tests.common import TransactionCase
_logger = logging.getLogger(__name__)


class TestSalesReturn(TransactionCase):
    """Sales Return Test Cases"""
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.test_company_6 = self.env.ref('base.main_company')
        self.warehouse = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', self.test_company_6.id),
             ('location_type', '=', 'view')], limit=1)
        self.transit_warehouse = self.env['stock.warehouse'].with_user(
            1).create([{
            'name': f'{self.test_company_6.name} Transit',
            'code': f'{self.test_company_6.name[:5]} Transit',
            'location_type': 'transit',
            'company_id': self.test_company_6.id,
            'partner_id': self.test_company_6.partner_id.id,
            'zip': self.test_company_6.zip,
            'street': self.test_company_6.street,
            'city': self.test_company_6.city,
            'county': self.test_company_6.county,
            'location_id': f'{self.test_company_6.name[:5]} Transit',
        }])
        self.customer = self.env['res.partner'].sudo().create([{
            'name': 'Partner 6',
            'zip': 90703,
            'is_customer': True,
            'type': 'contact',
            'po_no': 'TEST123',
        }])
        self.categ_id = self.env['product.category'].sudo().create(
            [{'name': 'Test Category'}])
        self.base_uom = self.env.ref('uom.product_uom_unit')
        self.product = self.env['product.product'].sudo().create([{
            'name': 'Product 1',
            'product_type': 'product',
            'uom_id': self.base_uom.id,
            'list_price_1': 100,
            'categ_id': self.categ_id.id,
        }])
        # Create sale order
        self.sale_order = self.env['sale.order'].sudo().create([{
            'partner_id': self.customer.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 4,
                'unit_price': 20.0
            })]
        }])
        company_invoice_sequence = {
            'name': 'Invoice Sequence',
            'prefix': 'INV/',
            'inv_seq': True,
            'padding': 4,
            'company_id': self.test_company_6.id,
        }
        invoice_sequence = self.env['ir.sequence'].sudo().create(
            [company_invoice_sequence])
        self.env['default.receivable'].with_user(1).create(
            [{'company_id': self.test_company_6.id,
              'inv_seq_id': invoice_sequence.id}])
        self.test_company_6.load_coa()
        self.packing_slip = self.env['packing.slip'].sudo().create([{
            'company_id': self.test_company_6.id,
            'state': 'in_progress',
        }])
        # Create sale order detail
        self.sale_detail = self.env['sale.order.details'].sudo().create([{
            'packing_slip_id': self.packing_slip.id,
            'sale_id': self.sale_order.id,
            'partner_id': self.customer.id,
            'state': 'confirm',
            'pack_slip_check': True,
            'company_id': self.test_company_6.id,
        }])
        self.pick_list = self.env['picking.list'].sudo().create({
            'product_id': self.product.id,
            'sale_id': self.sale_order.id,
            'warehouse_id': self.warehouse.id,
            'transit_warehouse_id': self.transit_warehouse.id,
            'picked_qty': 10,
            'quantity_done': 0,
            'state': 'confirm',
        })
        # Create journal
        self.journal = self.env['account.journal'].sudo().create([{
            'name': 'Test Sale Journal',
            'type': 'sale',
            'code': 'TSJ',
            'company_id': self.test_company_6.id,
        }])
        self.invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_date': date.today(),
            'sale_id': self.sale_order.id,
            'pack_slip_id':self.packing_slip.id,
            'company_id': self.test_company_6.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 5,
                'price_unit': 20,
            })]
        })
        self.sale_detail.invoice_id = self.invoice
        self.delivery_move = self.env['delivery.packing.slip'].sudo().create({
            'packing_slip_id': self.packing_slip.id,
            'sale_order_detail_ids': [self.sale_detail.id],
            'pick_list_ids': [self.pick_list.id],
            'delivery_move_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'sale_id': self.sale_order.id,
                'sale_line_id': self.sale_order.order_line[0].id,
                'transit_warehouse_id': self.transit_warehouse.id,
                'deliver_qty': 5,
                'sale_uom': self.base_uom.id,
                'pick_list_id': self.pick_list.id,
            })]
        })
        # Confirm delivery
        self.delivery_move.action_confirm_delivery()
        # Create base values for sales return
        self.base_sales_return_vals = {
            'partner_id': self.customer.id,
            'invoice_id': self.invoice.id,  # Required field
            'return_from': 'customer',
            'warehouse_id': self.warehouse.id
        }

    def test_compute_invoice_ids(self):
        """Test computation of invoice_ids based on partner"""
        sales_return = self.env['sales.return'].sudo().create(self.base_sales_return_vals)
        sales_return._compute_invoice_ids()
        self.assertIn(self.invoice.id, sales_return.invoice_ids.ids)

    def test_onchange_partner_id(self):
        """Test reset of fields when partner changes"""
        sales_return = self.env['sales.return'].sudo().create([{
            **self.base_sales_return_vals,
            'sale_id': self.sale_order.id
        }])
        sales_return._onchange_partner_id()
        self.assertFalse(sales_return.sale_id)
        self.assertFalse(sales_return.invoice_id)

    def test_onchange_invoice_id(self):
        """Test creation of return lines when invoice changes"""
        sales_return = self.env['sales.return'].sudo().create(
            self.base_sales_return_vals)
        sales_return._onchange_invoice_id()
        self.assertEqual(len(sales_return.sale_return_line_ids), 1)
        self.assertEqual(sales_return.sale_return_line_ids.product_id,
                         self.product)

    def test_create_method(self):
        """Test creation of sales return with sequence"""
        sales_return = self.env['sales.return'].sudo().create(
            self.base_sales_return_vals)
        self.assertTrue(sales_return.name.startswith('RTN/'))
        # Test duplicate draft return for same invoice
        with self.assertRaises(ValidationError):
            self.env['sales.return'].create(self.base_sales_return_vals)

    def test_action_return(self):
        """Test stock return process"""
        return_vals = {
            **self.base_sales_return_vals,
            'sale_return_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'returning_qty': 2,
                'sale_uom': self.product.uom_id.id
            })]
        }
        sales_return = self.env['sales.return'].sudo().create(return_vals)
        sales_return.action_return()
        self.assertEqual(sales_return.state, 'done')
        self.assertTrue(sales_return.picking_id)
        # Test with no return quantity
        with self.assertRaises(UserError):
            sales_return2 = self.env['sales.return'].sudo().create(
                self.base_sales_return_vals)
            sales_return2.action_return()

    def test_action_cancel(self):
        """Test cancellation of sales return"""
        sales_return = self.env['sales.return'].sudo().create(
            self.base_sales_return_vals)
        sales_return.action_cancel()
        self.assertEqual(sales_return.state, 'cancel')

    def test_unlink(self):
        """Test deletion restrictions"""
        sales_return = self.env['sales.return'].sudo().create({
            **self.base_sales_return_vals,
            'state': 'done'
        })
        with self.assertRaises(UserError):
            sales_return.unlink()
        # Should allow deleting draft records
        sales_return2 = self.env['sales.return'].sudo().create(
            self.base_sales_return_vals)
        sales_return2.unlink()

