import logging

# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
_logger = logging.getLogger(__name__)


class TestResCompany(TransactionCase):

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

    def test_create_company_with_defaults(self):
        """Tests for ensuring the default records are creating properly for a company creation."""

        new_company = self.env['res.company'].create([{
            'name': 'New Test Company',
            'email': 'company.newtest@example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])

        # Verify CRV Tax was created
        crv_tax = self.env['account.tax'].search([
            ('name', '=', 'CRV 5 Cents'),
            ('company_id', '=', new_company.id)
        ], limit=1)
        self.assertTrue(crv_tax, "CRV Tax was not created")
        self.assertEqual(crv_tax.amount, 0.05, "CRV Tax amount is incorrect")

        # Verify UoM Category was created
        uom_category = self.env['uom.category'].search([
            ('name', '=', 'Unit'),
        ], limit=1)
        self.assertTrue(uom_category, "UoM Category was not created")

        # Verify UoM was created
        uom = self.env['uom.uom'].search([
            ('name', '=', 'Each'),
            ('company_id', '=', new_company.id)
        ], limit=1)
        self.assertTrue(uom, "UoM 'Each' was not created")

        # Verify Product Category was created
        product_category = self.env['product.category'].search([
            ('name', '=', 'Default Category'),
            ('company_id', '=', new_company.id)
        ], limit=1)
        self.assertTrue(product_category, "Default Product Category was not created")
        _logger.info("test_create_company_with_defaults passed")