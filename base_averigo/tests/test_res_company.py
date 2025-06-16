# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestResCompany(TransactionCase):
    """Test case for res company"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Operator = cls.env['res.company']
        cls.config_parameter = cls.env['ir.config_parameter']

    def test_onchange_operator_name(self):
        """Test that operator name change will update other fields value."""
        self.config_parameter.set_param('web.base.url', 'http://192.168.1.1:8069')
        operator = self.Operator.create([{
            'name': 'Test Operator',
            'email': 'test@example.com',
            'zip': 90001
        }])
        operator._onchange_operator_name()
        self.assertEqual(operator.operator_domain, 'testoperator')
        self.assertEqual(operator.base_domain, '.averigo.com')
        self.assertEqual(operator.exact_domain, 'http://testoperator.averigo.com')
        self.config_parameter.set_param('web.base.url', 'http://example.com:8069')
        operator._onchange_operator_name()
        self.assertEqual(operator.base_domain, '.example.com')
        self.assertEqual(operator.exact_domain, 'http://testoperator.example.com')
        operator.operator_domain = 'customdomain'
        operator._onchange_operator_name()
        self.assertEqual(operator.operator_domain, 'customdomain')
        self.assertEqual(operator.exact_domain, 'http://customdomain.example.com')
        _logger.info('test_onchange_operator_name passed')

    def test_get_address(self):
        """Test that a valid ZIP code updates the address fields correctly."""
        operator = self.Operator.create([{
            'name': 'Test Operator',
            'email': 'test@example.com',
            'zip': 90001
        }])
        operator.get_address()
        self.assertEqual(operator.city, 'Los Angeles')
        self.assertEqual(operator.state_id.name, 'California')
        self.assertEqual(operator.county, 'Los Angeles County')
        self.assertEqual(operator.state_id.country_id.name, 'United States')
        _logger.info('test_get_address passed')

    def test_get_address_invalid_zip(self):
        """Test that an invalid ZIP code raises a ValidationError."""
        operator = self.Operator.create([{
            'name': 'Test Operator',
            'email': 'test@example.com',
            'zip': '90001'
        }])
        with self.assertRaises(ValidationError):
            operator.zip = 99999
            operator.get_address()
        _logger.info('test_get_address_invalid_zip passed')