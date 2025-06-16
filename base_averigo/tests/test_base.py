# -*- coding: utf-8 -*-
import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestBase(TransactionCase):
    """Test case for validation function in base model"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_model = cls.env['base']

    def test_valid_averigo_email_validation(self):
        """Test valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.in"
        ]
        for email in valid_emails:
            self.base_model.averigo_email_validation(email)
        _logger.info('test_valid_averigo_email_validation passed')

    def test_invalid_averigo_email_validation(self):
        """Test invalid email addresses"""
        invalid_emails = [
            "plainaddress",
            "missing@dotcom",
        ]
        for email in invalid_emails:
            with self.assertRaises(ValidationError):
                self.base_model.averigo_email_validation(email)
        _logger.info('test_invalid_averigo_email_validation passed')

    def test_valid_phone(self):
        """Test valid US phone numbers"""
        valid_phones = [
            "123-456-7890",
            "(123) 456-7890",
        ]
        for phone in valid_phones:
            self.base_model.averigo_phone_validation(phone)
        _logger.info('test_valid_phone passed')

    def test_invalid_phone(self):
        """Test invalid phone numbers"""
        invalid_phones = [
            "12345",
            "abcdefg",
        ]
        for phone in invalid_phones:
            with self.assertRaises(ValidationError):
                self.base_model.averigo_phone_validation(phone)
        _logger.info('test_invalid_phone passed')

