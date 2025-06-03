# -*- coding: utf-8 -*-

import logging
from odoo.exceptions import UserError
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestResPartner(common.TransactionCase):
    """Partner test cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.partner = self.env['res.partner']

    def test_child_count_zero_when_not_frontend(self):
        # Compute child_count as 0 when is_frontend_boolean is False
        _logger.info('Test start child count')
        partner = self.partner.create([{
            'name': 'Test Partner',
            'is_frontend_boolean': False,
            'company_id': self.env.company.id
        }])
        partner._compute_child_count()
        self.assertEqual(partner.child_count, 0)
        _logger.info('Test end child count')

    def test_child_count_no_company(self):
        # Handle case when company_id is not set
        partner = self.partner.create([{
            'name': 'Test Partner',
            'is_frontend_boolean': True,
            'company_id': False
        }])
        partner._compute_child_count()
        self.assertEqual(partner.child_count, 0)

    def test_get_child_list_returns_correct_action(self):
        # Returns dictionary with correct window action type and name for child list view

        partner = self.partner.create([{'name': 'Test Partner'}])
        list_view = self.env.ref(
            'averigo_base_customer.res_partner_tree_view_base_averigo')
        result = partner.action_child_list()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['name'], "child's")
        self.assertEqual(result['view_mode'], 'list')
        self.assertEqual(result['res_model'], 'res.partner')
        self.assertEqual(result['views'], [(list_view.id, 'list')])
        self.assertEqual(result['domain'],
                         [('parent_partner_id', '=', partner.id)])
        self.assertEqual(result['context'], "{'create': False}")

    def test_both_subsidies_raises_error(self):
        # Setting both subsidy_amount and subsidy_percentage raises UserError
        partner = self.partner.create([{'name': 'Test Partner'}])
        partner.subsidy_amount = 1000
        partner.subsidy_percentage = 50
        with self.assertRaises(UserError) as context:
            partner._onchange_subsidy_amount()
        self.assertEqual(
            str(context.exception),
            "You cannot give two subsidy method at same time.")

    def test_subsidy_percentage_raises_error(self):
        # Setting subsidy_percentage > 100% raises UserError
        partner = self.partner.create([{'name': 'Test Partner'}])
        partner.subsidy_percentage = 500
        with self.assertRaises(UserError) as context:
            partner._onchange_subsidy_amount()
        self.assertEqual(
            str(context.exception),
            "Subsidy Percentage should be between 0% to 100%!")

    def test_compute_contract_count_updates_on_change(self):
        # Compute contracts_count field when contracts_count dependency changes
        partner = self.partner.create([{'name': 'Test Partner'}])
        # Initial count should be 0
        partner._compute_contract_count()
        self.assertEqual(partner.contracts_count, 0)
        # Create a contract for this partner
        self.env['customer.contract'].create([{
            'partner_id': partner.id,
            'name': 'Test Contract'
        }])
        # Count should update to 1
        partner._compute_contract_count()
        self.assertEqual(partner.contracts_count, 1)

    def test_contact_type_sets_contact_type_address(self):
        # Type 'contact' sets type_address to 'contact'
        partner = self.partner.create([{
            'name': 'Test Partner',
            'type': 'contact'
        }])
        partner._compute_type_portal()
        self.assertEqual(partner.type_address, 'contact')

    def test_duplicate_primary_true_for_multiple_primary_contacts(self):
        # Method correctly sets duplicate_primary to True when multiple child contacts are marked as primary
        partner = self.partner.create([{'name': 'Test Partner'}])
        child1 = self.partner.create([{
            'name': 'Child 1',
            'parent_id': partner.id,
            'is_primary': True
        }])
        child2 = self.partner.create([{
            'name': 'Child 2',
            'parent_id': partner.id,
            'is_primary': True
        }])
        partner._compute_primary_contact_details()
        self.assertTrue(partner.duplicate_primary)

    def test_duplicate_primary_false_when_no_children(self):
        # Behavior when child_ids is empty list
        partner = self.partner.create([{'name': 'Test Partner'}])
        partner._compute_primary_contact_details()
        self.assertFalse(partner.duplicate_primary)

    def test_prevent_multiple_primary_contacts(self):
        # Multiple contacts marked as primary simultaneously
        partner = self.partner.create([{
            'name': 'Test Partner',
            'duplicate_primary': True
        }])
        contact1 = self.partner.create([{
            'name': 'Primary Contact',
            'parent_id': partner.id,
            'is_primary': True
        }])
        contact2 = self.partner.create([{
            'name': 'Second Contact',
            'parent_id': partner.id,
            'is_primary': True
        }])
        with self.assertRaises(UserError) as context:
            contact2._onchange_is_primary()
        self.assertEqual(
            str(context.exception),
            "Customer or address can only have one primary "
                              "contact!")

    def test_valid_zip_updates_address_fields(self):
        # Valid zip code updates state_id, city and county fields from zip.county record
        partner = self.partner.create([{'name': 'Test Partner'}])
        country = self.env['res.country'].search([('code', '=', 'US')], limit=1)
        state = self.env['res.country.state'].search(
            [('code', '=', 'NY'), ('country_id', '=', country.id)], limit=1)
        partner.zip = '12345'
        partner.get_zip_address()
        self.assertEqual(partner.state_id.id, state.id)
        self.assertEqual(partner.city, 'Schenectady')
        self.assertEqual(partner.county, 'Schenectady County')


    def test_invalid_zip_updates_address_fields(self):
        # inValid zip code error
        partner = self.partner.create([{'name': 'Test Partner'}])
        partner.zip = '00000'
        with self.assertRaises(UserError) as context:
            partner.get_zip_address()
        self.assertEqual(
            str(context.exception),
            "Invalid zip code.Please try again.")



