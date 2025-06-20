# -*- coding: utf-8 -*-

import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestMultiCompanyUsers(common.TransactionCase):
    """Multi Company User test cases"""

    def setUp(self):
        super(TestMultiCompanyUsers, self).setUp()
        self.Users = self.env['res.users']

    def test_create_supervisor_user(self):
        """Test creating a user with is_supervisor=True sets email and company_id"""
        user_vals = {
            'name': 'Supervisor User',
            'login': 'supervisor@example.com',
            'is_supervisor': True,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],  # Required field
        }
        user = self.Users.create(user_vals)
        self.assertEqual(user.email, 'supervisor@example.com', "Email should match login for supervisor")
        self.assertEqual(user.company_id.id, 1, "Company ID should be 1 for supervisor")

    def test_create_regular_user(self):
        """Test creating a user without is_supervisor does not auto-set fields"""
        user_vals = {
            'name': 'Regular User',
            'login': 'regular@example.com',
            'is_supervisor': False,
            'company_id': 1,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        }
        user = self.Users.create(user_vals)
        self.assertNotEqual(user.company_id.id, 1, "Company ID should not be automatically set to 1")
