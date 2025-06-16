# -*- coding: utf-8 -*-
import logging
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestIrHttp(TransactionCase):
    """Test case for datetime format"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.IrHttp = cls.env['ir.http']
        cls.company = cls.env.ref('base.main_company')

        cls.company.date_format_selection = "%m/%d/%Y"
        cls.company.time_format_selection = "%H:%M:%S"

    def test_date_time_format(self):
        """ Test if the date and time formats are correctly retrieved """
        lang = "en_US"
        _, lang_params = self.env["ir.http"].get_translations_for_webclient(["base"], lang)
        self.assertEqual(lang_params["date_format"], "%m/%d/%Y")
        self.assertEqual(lang_params["time_format"], "%H:%M:%S")
        _logger.info('test_date_time_format passed')
