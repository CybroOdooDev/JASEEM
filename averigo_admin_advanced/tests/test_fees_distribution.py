# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestFeesDistribution(TransactionCase):

    def setUp(self):
        super(TestFeesDistribution, self).setUp()
        self.fees_dist = self.env['fees.distribution'].create({
            'name': 'Test Distribution'
        })

        # Create test companies
        self.company_1 = self.env['res.company'].create([{
            'name': 'New Test Company',
            'email': 'company.newtest@example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])
        self.company_2 = self.env['res.company'].create([{
            'name': 'New Test Company2',
            'email': 'company.newtest2@example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])

        # Create micro market warehouses
        self.mm1 = self.env['stock.warehouse'].create({
            'name': 'MM1', 'code': 'MM1', 'company_id': self.company_1.id,
            'location_type': 'micro_market'
        })
        self.mm2 = self.env['stock.warehouse'].create({
            'name': 'MM2', 'code': 'MM2', 'company_id': self.company_2.id,
            'location_type': 'micro_market'
        })

        # Create test distributions
        self.dist1 = self.env['fees.distribution'].create({
            'name': 'Dist 1', 'company_ids': [(6, 0, [self.company_1.id])]
        })
        self.dist2 = self.env['fees.distribution'].create({
            'name': 'Dist 2', 'company_ids': [(6, 0, [self.company_2.id])]
        })

    def test_compute_dom_mm_ids_with_companies(self):
        """Test domain computation with selected companies"""
        self.dist1._compute_dom_mm_ids()
        self.assertEqual(self.dist1.dom_mm_ids, self.mm1)


    def test_excludes_assigned_micro_markets(self):
        """Test exclusion of already assigned micro markets"""
        self.dist1.micro_market_ids = [(6, 0, [self.mm1.id])]
        self.dist2.company_ids = [(6, 0, [self.company_1.id])]
        self.dist2._compute_dom_mm_ids()
        self.assertNotIn(self.mm1, self.dist2.dom_mm_ids)

    def test_compute_platform_fees_per_day_fixed_type(self):
        """Test platform fees per day calculation for fixed type"""
        self.fees_dist.platform_fees = 1200.0
        self.fees_dist.platform_fees_type = 'fixed'
        self.fees_dist._compute_platform_fees_per_day()

        # Expected: (1200 * 12) / 365 = 39.45 (approximately)
        expected = (1200 * 12) / 365
        self.assertAlmostEqual(self.fees_dist.platform_fees_per_day, expected,
                               places=2)

    def test_compute_platform_fees_per_day_percentage_type(self):
        """Test platform fees per day calculation for percentage type"""
        self.fees_dist.platform_fees = 1200.0
        self.fees_dist.platform_fees_type = 'percentage'
        self.fees_dist._compute_platform_fees_per_day()

        self.assertEqual(self.fees_dist.platform_fees_per_day, 0)

    def test_compute_platform_fees_per_day_zero_amount(self):
        """Test platform fees per day calculation with zero amount"""
        self.fees_dist.platform_fees = 0.0
        self.fees_dist.platform_fees_type = 'fixed'
        self.fees_dist._compute_platform_fees_per_day()

        self.assertEqual(self.fees_dist.platform_fees_per_day, 0)