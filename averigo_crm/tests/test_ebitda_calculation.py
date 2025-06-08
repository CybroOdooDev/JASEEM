from odoo.tests.common import TransactionCase


class TestCrmLead(TransactionCase):
    def setUp(self):
        super(TestCrmLead, self).setUp()
        # Create a test stage with a percentage
        self.stage = self.env['crm.stage'].create({
            'name': 'Test Stage',
            'stage_percentage': 50.0,
        })

        # Create a test lead
        self.lead = self.env['crm.lead'].create({
            'name': 'Test Lead',
            'ebitda': 1000.0,
            'stage_id': self.stage.id,
            'is_dynamic_crm_stage': True,
            'expected_revenue': 2000.0,
        })

    def test_compute_weighted_ebitda_dynamic_stage(self):
        """Test weighted_ebitda computation when is_dynamic_crm_stage is True"""
        self.lead._compute_weighted_ebitda()
        expected_weighted_ebitda = self.lead.ebitda * (
                self.stage.stage_percentage / 100)
        self.assertEqual(
            self.lead.weighted_ebitda,
            expected_weighted_ebitda,
            f"Expected weighted_ebitda to be {expected_weighted_ebitda}, got {self.lead.weighted_ebitda}"
        )

    def test_compute_weighted_ebitda_non_dynamic_stage(self):
        """Test weighted_ebitda computation when is_dynamic_crm_stage is False"""
        self.lead.is_dynamic_crm_stage = False
        self.lead._compute_weighted_ebitda()
        self.assertEqual(
            self.lead.weighted_ebitda,
            self.lead.expected_revenue,
            f"Expected weighted_ebitda to be {self.lead.expected_revenue}, got {self.lead.weighted_ebitda}"
        )

    def test_compute_weighted_ebitda_zero_percentage(self):
        """Test weighted_ebitda when stage_percentage is 0"""
        self.stage.stage_percentage = 0
        self.lead._compute_weighted_ebitda()
        self.assertEqual(
            self.lead.weighted_ebitda,
            0,
            f"Expected weighted_ebitda to be 0, got {self.lead.weighted_ebitda}"
        )

    def test_compute_weighted_ebitda_zero_expected_revenue(self):
        """Test weighted_ebitda when expected_revenue is 0 and is_dynamic_crm_stage is False"""
        self.lead.is_dynamic_crm_stage = False
        self.lead.expected_revenue = 0
        self.lead._compute_weighted_ebitda()
        self.assertEqual(
            self.lead.weighted_ebitda,
            0,
            f"Expected weighted_ebitda to be 0, got {self.lead.weighted_ebitda}"
        )
