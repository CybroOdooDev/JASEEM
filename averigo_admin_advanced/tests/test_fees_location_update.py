# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestFeesLocationUpdate(TransactionCase):

    def setUp(self):
        super().setUp()

        self.company_1 = self.env['res.company'].create([{
            'name': 'New Test Company',
            'email': 'company.newtest@example.com',
            'country_id': self.env.ref('base.us').id,
            'currency_id': self.env.ref('base.USD').id,
        }])

        # Create test warehouse
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TW01',
            'company_id': self.company_1.id,
            'location_type': 'micro_market'
        })

        # Create test fees template
        self.fees_template = self.env['fees.distribution'].create({
            'name': 'Test Fees Template',
            'cc_fees': 2.5,
            'app_fees': 1.5,
            'stored_fund_fees': 0.5,
            'platform_fees': 3.0,
            'room_cc': 100.0,
            'cash_adj': 50.0,
            'group_base_factor': 'margin',
            'group_fees_percentage': 5.0,
            'additional_group1_fees_percentage': 2.0,
            'brand_fees_percentage': 4.0,
            'management_fees_percentage': 6.0,
            'purchasing_group_fees_percentage': 3.5,
            'national_sales_fees_percentage': 7.0,
            'local_sales_fees_percentage': 8.0,
        })

    def test_process_updates_warehouse_fields(self):
        """Test that process() correctly updates warehouse with fees template values"""

        # Create fees location update wizard
        wizard = self.env['fees.location.update'].create({
            'fees_template_id': self.fees_template.id,
            'select_micro_market': 'select',
            'list_micro_market_id': [(6, 0, [self.warehouse.id])]
        })

        # Execute process
        wizard.process()

        # Verify warehouse fields are updated
        self.assertEqual(self.warehouse.fees_template_id.id, self.fees_template.id)
        self.assertEqual(self.warehouse.cc_fees, 2.5)
        self.assertEqual(self.warehouse.app_fees, 1.5)
        self.assertEqual(self.warehouse.stored_fund_fees, 0.5)
        self.assertEqual(self.warehouse.platform_fees, 3.0)
        self.assertEqual(self.warehouse.room_cc, 100.0)
        self.assertEqual(self.warehouse.cash_adj, 50.0)
        self.assertEqual(self.warehouse.group_fees_percentage, 5.0)
        self.assertEqual(self.warehouse.additional_fees1, 2.0)
        self.assertEqual(self.warehouse.brand_fees, 4.0)
        self.assertEqual(self.warehouse.management_fees, 6.0)
        self.assertEqual(self.warehouse.purchasing_group_fees_percentage, 3.5)
        self.assertEqual(self.warehouse.national_sales_fees_percentage, 7.0)
        self.assertEqual(self.warehouse.local_sales_fees_percentage, 8.0)
        # Note: There's a bug in the original code - platform_fees_per_day gets local_sales_fees_percentage

    def test_process_with_all_micromarkets(self):
        """Test process() with 'all' selection mode"""

        wizard = self.env['fees.location.update'].create({
            'fees_template_id': self.fees_template.id,
            'select_micro_market': 'all',
            'micro_market_ids': [(6, 0, [self.warehouse.id])]
        })

        wizard.process()

        # Verify warehouse is updated
        self.assertEqual(self.warehouse.fees_template_id.id,
                         self.fees_template.id)
        self.assertEqual(self.warehouse.cc_fees, 2.5)
