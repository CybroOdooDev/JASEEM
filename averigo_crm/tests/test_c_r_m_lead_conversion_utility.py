from odoo.tests.common import TransactionCase


class TestCrmLeadToOpportunity(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a sales team
        self.team = self.env['crm.team'].create({
            'name': 'Sales Team Test'
        })

        # Create a user (salesperson)
        self.user = self.env.ref('base.user_demo')

        # Create a test CRM lead
        self.lead = self.env['crm.lead'].create({
            'name': 'Test Lead',
            'contact_name': 'John Doe',
            'email_from': 'john@example.com',
            'team_id': self.team.id,
            'user_id': False,
        })

        # Create the wizard with context for active_ids
        self.wizard = self.env['crm.lead2opportunity.partner'].with_context(
            active_ids=self.lead.ids
        ).create({
            'action': 'create',
            'team_id': self.team.id,
            'user_id': self.user.id,
        })

    def test_create_customer(self):
        # Run the create_customer method
        result = self.wizard.create_customer()

        # Refresh lead to get updated values
        self.lead.refresh()

        # Check that a partner has been assigned or created
        self.assertTrue(self.lead.partner_id,
                        "Lead should be linked to a partner")

        # Check that the partner is now a customer if the opportunity is won
        self.lead.partner_id.write({'customer_rank': 1})
        self.assertGreater(self.lead.partner_id.customer_rank, 0,
                           "Partner should be a customer")

        # Check redirection result
        self.assertIn('res_model', result)
        self.assertEqual(result['res_model'], 'res.partner')
        self.assertEqual(result['res_id'], self.lead.partner_id.id)
