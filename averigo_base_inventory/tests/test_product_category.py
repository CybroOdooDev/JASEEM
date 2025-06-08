# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class TestProductCategory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref('base.main_company')

        cls.category1 = cls.env['product.category'].create([{
            'name': 'Test Category',
            'company_id': cls.company.id,
            'category_code': 'CAT001',
            'internal_reference': 'SAP123',
        }])

    def test_create_category(self):
        """Test successful creation of a Product Category."""
        category = self.env['product.category'].create([{
            'name': 'New Category',
            'company_id': self.company.id,
            'category_code': 'CAT002',
        }])
        self.assertEqual(category.name, 'New Category')
        self.assertEqual(category.company_id, self.company)
        self.assertEqual(category.category_code, 'CAT002')
        _logger.info('test_create_category passed')


    def test_copy_method(self):
        """Test that the copied category has a unique name."""
        category_copy = self.category1.copy()
        self.assertTrue("(copy)" in category_copy.name)
        self.assertNotEqual(self.category1.id, category_copy.id)
        _logger.info('test_copy_method passed')


