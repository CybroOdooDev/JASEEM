# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase
_logger = logging.getLogger(__name__)

class TestMultipleUoM(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductUoM = cls.env['multiple.uom']
        cls.ProductTemplate = cls.env['product.template']
        cls.UoM = cls.env['uom.uom']
        cls.CustomUoMTypes = cls.env['custom.uom.types']
        cls.ResCompany = cls.env['res.company']
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

        # Create a company
        cls.company = cls.ResCompany.create([{
            'name': 'Test Company',
            'country_id': cls.env.ref('base.us').id,
            'zip': 90001,
        }])

        # Create a product template
        cls.product_template = cls.ProductTemplate.create([{
            'name': 'Test Product',
            'standard_price': 10.0,
            'categ_id': cls.env.ref('product.product_category_all').id,
            'uom_id': cls.UoM.create([{
                'name': 'Custom UoM',
                'uom_type': 'bigger',
                'ratio': 2,
                'category_id': cls.env.ref('uom.product_uom_categ_unit').id
            }]).id,
        }])

        # Create a custom UoM type
        cls.custom_uom_type = cls.CustomUoMTypes.create([{
            'name': 'Test UoM Type',
            'company_id': cls.company.id,
        }])

    def test_create_product_uom(self):
        """Test creation of a new ProductUoM record."""
        product_uom = self.ProductUoM.create([{
            'name': 'Test UoM',
            'quantity': 5,
            'uom_template_id': self.product_template.id,
            'type': self.custom_uom_type.id,
        }])

        self.assertEqual(product_uom.name, 'Test UoM')
        self.assertEqual(product_uom.quantity, 5)
        self.assertEqual(product_uom.uom_template_id, self.product_template)
        self.assertEqual(product_uom.type, self.custom_uom_type)
        _logger.info('test_create_product_uom passed')

    def test_compute_standard_price(self):
        """Test the computation of the standard price."""
        product_uom = self.ProductUoM.create([{
            'name': 'Test UoM',
            'quantity': 5,
            'uom_template_id': self.product_template.id,
            'type': self.custom_uom_type.id,
        }])

        # Check if the standard price is computed correctly
        self.assertEqual(product_uom.standard_price, 50.0)  # 5 * 10.0
        _logger.info('test_compute_standard_price passed')

    def test_onchange_quantity(self):
        """Test the onchange method for quantity."""
        product_uom = self.ProductUoM.create([{
            'name': 'Test UoM',
            'quantity': 5,
            'uom_template_id': self.product_template.id,
            'type': self.custom_uom_type.id,
        }])

        # Change the quantity and trigger the onchange method
        product_uom.quantity = 10
        product_uom._onchange_standard_prices()

        # Check if the standard price is updated correctly
        self.assertEqual(product_uom.standard_price, 100.0)  # 10 * 10.0
        _logger.info('test_onchange_quantity passed')

    def test_onchange_type(self):
        """Test the onchange method for type."""
        product_uom = self.ProductUoM.create([{
            'name': 'Test UoM',
            'quantity': 5,
            'uom_template_id': self.product_template.id,
            'type': self.custom_uom_type.id,
        }])

        # Change the type and trigger the onchange method
        new_type = self.CustomUoMTypes.create([{
            'name': 'New UoM Type',
            'company_id': self.company.id,
        }])
        product_uom.type = new_type
        product_uom.onchange_type()

        # Check if the name is updated correctly
        self.assertEqual(product_uom.name, 'New UoM Type')
        _logger.info('test_onchange_type passed')

    def test_write_method(self):
        """Test the write method for updating the UoM."""
        product_uom = self.ProductUoM.create([{
            'name': 'Test UoM',
            'quantity': 5,
            'uom_template_id': self.product_template.id,
            'type': self.custom_uom_type.id,
        }])

        # Update the quantity and type
        new_type = self.CustomUoMTypes.create([{
            'name': 'New UoM Type',
            'company_id': self.company.id,
        }])
        product_uom.write({
            'quantity': 10,
            'type': new_type.id,
        })

        # Check if the UoM is updated correctly
        self.assertEqual(product_uom.quantity, 10)
        self.assertEqual(product_uom.type, new_type)
        self.assertEqual(product_uom.standard_price, 100.0)
        _logger.info('test_write_method passed')

    def test_create_multi(self):
        """Test creating multiple records at once."""
        vals_list = [
            {
                'name': 'Test UoM 1',
                'quantity': 5,
                'uom_template_id': self.product_template.id,
                'type': self.custom_uom_type.id,
            },
            {
                'name': 'Test UoM 2',
                'quantity': 10,
                'uom_template_id': self.product_template.id,
                'type': self.custom_uom_type.id,
            },
        ]

        product_uoms = self.ProductUoM.create(vals_list)

        # Check if both records are created correctly
        self.assertEqual(len(product_uoms), 2)
        self.assertEqual(product_uoms[0].name, 'Test UoM 1')
        self.assertEqual(product_uoms[0].quantity, 5)
        self.assertEqual(product_uoms[1].name, 'Test UoM 2')
        self.assertEqual(product_uoms[1].quantity, 10)
        _logger.info('test_create_multi passed')