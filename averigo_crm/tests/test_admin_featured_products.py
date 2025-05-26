import logging
from datetime import date, timedelta

from odoo import exceptions
from odoo.exceptions import ValidationError
import hashlib
from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestAdminFeaturedProducts(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.featured_pdt = cls.env['admin.featured.products']

        cls.Company = cls.env['res.company']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']
        cls.Category = cls.env['product.category']

        cls.customer = cls.Partner.create({
            'name': 'Test Customer',
            'is_customer': True,
            'operator_id': cls.env.company.id,
        })

        cls.micro_market = cls.env['stock.warehouse'].create({
            'name': 'Warehouse 2',
            'code': 'WH2',
            'company_id': cls.env.company.id,
        })
        cls.Product_category = cls.Category.create({
                    'name': 'Cool drinks',
                })

        cls.product = cls.Product.create({
            'name': 'Test Product',
            'categ_id': cls.Product_category.id
        })

        cls.product_2 = cls.Product.create({
            'name': 'Test Product2',
            'categ_id': cls.Product_category.id
        })
        print(cls.product)


    def test_create_triggers_compute(self):
        # Create record of your model (replace with actual model)
        featured_product = self.featured_pdt.create({
            'company_ids': [(6, 0, [self.env.company.id])],
            'location_ids': [(6, 0, [self.customer.id])],
            'micro_market_ids': [(6, 0, [self.micro_market.id])],
            'product_ids': [(6, 0, [self.product_2.id])],
            'start_date': str(date.today()),
            'end_date': str(date.today() + timedelta(days=1)),
            'start_time': 5.0,
            'end_time': 8.0,
        })
        self.assertTrue(featured_product)
        self.assertIn(self.micro_market.id, featured_product.micro_market_ids.ids)
        self.assertEqual(featured_product.start_time, 5.0)
        self.assertEqual(featured_product.end_time, 8.0)
        self.assertTrue(featured_product.update_date)

    def test_create_with_invalid_dates(self):
        """Test error is raised when end_date is before start_date."""
        with self.assertRaises(exceptions.UserError):
            self.featured_pdt.create({
                'start_date': str(date.today()),
                'end_date': str(date.today() - timedelta(days=1)),
                'start_time': 9.0,
                'end_time': 17.0,
            })

    def test_mm_ids_fallback_to_micro_market_ids(self):
        """Test that mm_ids is set from micro_market_ids if present."""
        featured_product = self.featured_pdt.create({
            'micro_market_ids': [(6, 0, [self.micro_market.id])],
            'start_time': 7.0,
            'end_time': 9.0,
        })
        self.assertEqual(featured_product.mm_ids.ids, [self.micro_market.id])

    def test_get_24_time_am_pm_conversion(self):
        """Test _get_24_time correctly converts to 24-hour float format."""

        # Example: 2:30:15 PM -> 14.30 (float)
        result_pm = self.featured_pdt._get_24_time(2.30, 'pm', 15)
        self.assertAlmostEqual(result_pm, 14.30, places=2)

        # Example: 9:15:00 AM -> 9.15 (float)
        result_am = self.featured_pdt._get_24_time(9.15, 'am', 0)
        self.assertAlmostEqual(result_am, 9.15, places=2)

        # Midnight case: 12:00:00 AM -> 0.00
        result_midnight = self.featured_pdt._get_24_time(12.00, 'am', 0)
        self.assertAlmostEqual(result_midnight, 0.00, places=2)

        # Noon case: 12:00:00 PM -> 12.00
        result_noon = self.featured_pdt._get_24_time(12.00, 'pm', 0)
        self.assertAlmostEqual(result_noon, 12.00, places=2)

        # No time given
        result_none = self.featured_pdt._get_24_time(False, 'am', 0)
        self.assertFalse(result_none)


