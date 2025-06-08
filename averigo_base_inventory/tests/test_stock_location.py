# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)

class TestStockLocation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
            'name': 'Test Company',
            'email': 'company.newtest@example.com',
            'country_id': cls.env.ref('base.us').id,
            'currency_id': cls.env.ref('base.USD').id,
        }])
        cls.warehouse = cls.env['stock.warehouse'].create([{
            'name': 'Test Warehouse',
            'code': 'TW',
            'company_id': cls.company.id
        }])
        cls.parent_location = cls.env['stock.location'].create([{
            'name': 'Parent Location',
            'usage': 'internal',
            'company_id': cls.company.id
        }])

    def test_create_bin_location(self):
        """Test creating a bin location and check computed values"""
        location = self.env['stock.location'].create([{
            'name': 'Bin A1',
            'is_bin_location': True,
            'warehouse_id': self.warehouse.id,
            'company_id': self.company.id,
        }])
        self.assertTrue(location.is_bin_location)
        self.assertEqual(location.complete_name, 'TW/Bin A1', "Computed complete_name is incorrect")
        _logger.info('test_create_bin_location passed')

    def test_create_non_bin_location(self):
        """Test creating a normal stock location (not a bin)"""
        location = self.env['stock.location'].create([{
            'name': 'Shelf 1',
            'location_id': self.parent_location.id,
            'is_bin_location': False,
            'company_id': self.company.id,
        }])
        self.assertFalse(location.is_bin_location)
        self.assertEqual(location.complete_name, f'{self.parent_location.complete_name}/Shelf 1')
        _logger.info('test_create_non_bin_location passed')

    def test_update_warehouse_id(self):
        """Test updating warehouse_id and verify location_id update"""
        location = self.env['stock.location'].create([{
            'name': 'Bin B2',
            'is_bin_location': True,
            'warehouse_id': self.warehouse.id,
            'company_id': self.company.id,
        }])
        new_warehouse = self.env['stock.warehouse'].create([{
            'name': 'New Warehouse',
            'code': 'NW',
            'company_id': self.company.id
        }])
        location.write({'warehouse_id': new_warehouse.id})
        self.assertEqual(location.complete_name, 'NW/Bin B2', "Warehouse update did not change complete_name correctly")
        _logger.info('test_update_warehouse_id passed')

