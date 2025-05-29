from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo import fields


class TestCRMLead(TransactionCase):
    def setUp(self):
        super(TestCRMLead, self).setUp()
        # Set up test data
        self.user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user@example.com',
            'email': 'test_user@example.com',
        })

        self.team = self.env['crm.team'].create({
            'name': 'Test Team',
            'user_ids': [(4, self.user.id)],
        })

        self.stage_new = self.env.ref('averigo_crm.stage_lead01')
        self.stage_site_survey = self.env.ref('averigo_crm.stage_lead02')
        self.stage_proposal = self.env.ref('averigo_crm.stage_lead03')
        self.stage_agreement = self.env.ref('averigo_crm.stage_lead04')
        self.stage_sow = self.env.ref('averigo_crm.stage_lead05')
        self.stage_won = self.env.ref('crm.stage_lead4')

        self.partner = self.env['res.partner'].create({
            'name': 'Test Partner',
            'is_customer': True,
            'type': 'contact',
            'email': 'partner@example.com',
        })

        self.zip_county = self.env['zip.county'].create({
            'zip': '12345',
            'city': 'Test City',
            'state': 'CA',
        })

        self.lead = self.env['crm.lead'].create({
            'name': 'Test Lead',
            'first_name': 'John',
            'middle_name': 'M',
            'last_name': 'Doe',
            'user_id': self.user.id,
            'team_id': self.team.id,
            'stage_id': self.stage_new.id,
            'partner_id': self.partner.id,
            'zip': '12345',
            'probability': 50,
        })

    def test_compute_stages(self):
        """Test stage computation logic"""
        # Test site survey stage
        self.lead.stage_id = self.stage_site_survey
        self.lead._compute_stages()
        self.assertTrue(self.lead.is_site_survey_stage)
        self.assertFalse(self.lead.is_proposal_stage)
        self.assertFalse(self.lead.is_agreement_stage)
        self.assertFalse(self.lead.is_sow_stage)
        self.assertFalse(self.lead.is_won_stage)

        # Test proposal stage
        self.lead.stage_id = self.stage_proposal
        self.lead._compute_stages()
        self.assertTrue(self.lead.is_proposal_stage)
        self.assertFalse(self.lead.is_site_survey_stage)
        self.assertFalse(self.lead.is_agreement_stage)
        self.assertFalse(self.lead.is_sow_stage)
        self.assertFalse(self.lead.is_won_stage)

        # Test won stage
        self.lead.stage_id = self.stage_won
        self.lead._compute_stages()
        self.assertTrue(self.lead.is_won_stage)
        self.assertFalse(self.lead.is_site_survey_stage)
        self.assertFalse(self.lead.is_proposal_stage)
        self.assertFalse(self.lead.is_agreement_stage)
        self.assertFalse(self.lead.is_sow_stage)

    def test_get_address(self):
        """Test address population based on ZIP code"""
        self.lead.zip = '12345'
        self.lead.get_address()
        state = self.env['res.country.state'].search([
            ('code', '=', 'CA'),
            ('country_id', '=', self.env.ref('base.us').id)
        ], limit=1)
        self.assertEqual(self.lead.city, 'Test City')
        self.assertEqual(self.lead.state_id.id, state.id)
        self.assertEqual(self.lead.zip, '12345')

    def test_create_lead(self):
        """Test lead creation with full name construction"""
        lead = self.env['crm.lead'].create({
            'name': 'Test Create Lead',
            'first_name': 'Jane',
            'middle_name': 'K',
            'last_name': 'Smith',
            'user_id': self.user.id,
            'team_id': self.team.id,
        })
        self.assertEqual(lead.contact_name, 'Jane K Smith')
        self.assertEqual(lead.stage_id.id, self.stage_new.id)
        self.assertTrue(lead.probability >= 0 and lead.probability <= 100)
