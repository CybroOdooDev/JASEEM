# -*- coding: utf-8 -*-
from . import models


def archive_default_categories(cr):
    """
    This function will be called after the module is installed.
    It archives the default product categories like 'All' and 'Deliveries'.
    """
    category_xml_ids = [
        'product.product_category_all',
        'product.cat_expense',
        'product.product_category_1',
    ]
    for category_xml_id in category_xml_ids:
        category = cr.ref(category_xml_id, raise_if_not_found=False)
        if category:
            category.active = False

def activate_default_categories(cr):
    """
    This function reactivates the default product categories when the module is uninstalled.
    """
    category_xml_ids = [
        'product.product_category_all',
        'product.cat_expense',
        'product.product_category_1',
    ]

    for category_xml_id in category_xml_ids:
        category = cr.ref(category_xml_id, raise_if_not_found=False)
        if category:
            category.active = True