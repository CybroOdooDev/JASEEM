# -*- coding: utf-8 -*-

import logging

from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError
from odoo import fields
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestCustomerContract(common.TransactionCase):
    """Contract test cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()

    def test_company_updated_to_operator_id(self):
        # When partner_id is set, contract company_id is updated to partner's operator_id if it exists
        partner = self.env['res.partner'].create([{
            'name': 'Test Partner',
            'operator_id': self.env.company.id,
        }])
        contract = self.env['customer.contract'].new({
            'name': 'Test Contract'
        })
        contract.partner_id = partner
        contract._onchange_partner_id()
        self.assertEqual(contract.company_id, partner.operator_id)

    def test_valid_contract_dates(self):
        # Contract with no overlapping dates should be validated successfully
        contract = self.env['customer.contract'].create([{
            'name': 'Test Contract',
            'date_start': fields.Date.today(),
            'date_end': fields.Date.today() + relativedelta(months=1)
        }])
        # Should not raise ValidationError
        contract._check_dates()

    def test_assign_contract_to_partner(self):
        # Contract successfully assigns itself as active contract to partner
        partner = self.env['res.partner'].create([{
            'name': 'Test Partner'
        }])
        contract = self.env['customer.contract'].create([{
            'partner_id': partner.id,
            'name': 'Test Contract'
        }])
        contract._assign_open_contract()
        self.assertEqual(partner.contract_id.id, contract.id)

    def test_overlapping_contracts(self):
        # Create a contract in 'open' state
        partner = self.env['res.partner'].create([{
            'name': 'Test Partner'
        }])
        contract1 = self.env['customer.contract'].create([{
            'name':'Contract 1',
            'partner_id': partner.id,
            'state': 'open',
            'date_start': '2023-01-01',
            'date_end': '2023-12-31',
        }])
        # Try to create another contract with overlapping dates
        with self.assertRaises(ValidationError):
            self.env['customer.contract'].create([{
                'name':'contract 2',
                'partner_id': partner.id,
                'state': 'open',
                'date_start': '2023-06-01',
                'date_end': '2024-06-01',
            }])

    def test_non_overlapping_contracts(self):
        partner = self.env['res.partner'].create([{
            'name': 'Test Partner'
        }])
        # Create a contract in 'open' state
        contract1 = self.env['customer.contract'].create([{
            'name': 'Contract 1',
            'partner_id': partner.id,
            'state': 'open',
            'date_start': '2023-01-01',
            'date_end': '2023-12-31',
        }])
        # Create another contract with non-overlapping dates
        contract2 = self.env['customer.contract'].create([{
            'name': 'Contract 2',
            'partner_id': partner.id,
            'state': 'open',
            'date_start': '2024-01-01',
            'date_end': '2024-12-31',
        }])
        # No exception should be raised
        self.assertTrue(contract2)
