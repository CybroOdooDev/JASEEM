# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestStockQuant(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockQuant = cls.env['stock.quant']
        cls.StockLocation = cls.env['stock.location']
        cls.StockWarehouse = cls.env['stock.warehouse']
        cls.ProductProduct = cls.env['product.product']
        cls.ProductTemplate = cls.env['product.template']
        cls.Uom = cls.env['uom.uom']
        cls.ProductCategory = cls.env['product.category']
        cls.Company = cls.env['res.company']
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

        cls.company = cls.Company.create([{
            'name': 'New Test Company',
            'email': 'company.newtest@example.com',
            'country_id': cls.env.ref('base.us').id,
            'currency_id': cls.env.ref('base.USD').id,
        }])
        cls.warehouse = cls.StockWarehouse.create([{
            'name': 'Test Warehouse',
            'code': 'TW',
        }])
        cls.location = cls.StockLocation.create([{
            'name': 'Stock Location',
            'usage': 'internal',
        }])
        cls.product_category = cls.ProductCategory.create([{
            'name': 'Test Category',
        }])
        cls.uom = cls.Uom.create([{
            'name': 'Test UoM',
            'category_id': cls.env.ref('uom.product_uom_categ_unit').id,
            'uom_type': 'bigger',
            'company_id': cls.company.id,
        }])
        cls.product_template = cls.ProductTemplate.create([{
            'name': 'Test Product',
            'categ_id': cls.product_category.id,
            'product_type': 'product',
            'uom_id': cls.uom.id,
            'uom_po_id': cls.uom.id,
            'is_storable': True,
        }])
        cls.product_variant = cls.product_template.product_variant_ids[0]
        cls.quant = cls.StockQuant.create([{
            'product_id': cls.product_variant.id,
            'location_id': cls.location.id,
            'quantity': 10.0,
            'reserved_quantity': 2.0,
        }])

    def test_compute_inventory_quantity(self):
        """Test the computation of the inventory quantity for a stock quant."""
        self.quant._compute_inventory_quantity()
        self.assertEqual(self.quant.inventory_quantity, 10.0, "Inventory quantity computation is incorrect")
        _logger.info('test_compute_inventory_quantity passed')

    def test_compute_warehouse_id(self):
        """Test the computation of the warehouse ID for a stock quant based on its location."""
        self.location.is_bin_location = True
        self.location.warehouse_id = self.warehouse
        self.quant.compute_warehouse_id()
        self.assertEqual(self.quant.warehouse_id, self.warehouse, "Warehouse ID computation is incorrect")
        _logger.info('test_compute_warehouse_id passed')
