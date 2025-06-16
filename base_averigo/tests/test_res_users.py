# -*- coding: utf-8 -*-
import logging

from odoo.tests.common import TransactionCase
_logger = logging.getLogger(__name__)

class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.User = cls.env['res.users']

    def test_onchange_full_name(self):
        """"""
        user = self.User.create([{
            'first_name': 'Test',
            'last_name': 'User',
            'name': 'Test User',
            'login': 'test_user',
        }])
        user._onchange_full_name()
        self.assertEqual(user.name, 'Test User')
        user.write({
            'first_name': 'John',
            'last_name': 'Doe',
        })
        user._onchange_full_name()
        self.assertEqual(user.name, 'John Doe')
        _logger.info('test_get_address passed')

