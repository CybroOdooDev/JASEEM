# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import common

class TestEmployeeDiscount(common.TransactionCase):
    """Employee Discount test cases"""

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.employee_discount = self.env['employee.discount.setup']
        self.customer1 = self.env['res.partner'].create(
            [{'name': 'Customer 1', 'zip': 90703}]).id
        self.customer2 = self.env['res.partner'].create(
            [{'name': 'Customer 2', 'zip': 90704}]).id
        self.mm1 = self.env['stock.warehouse'].create([{
            'name': 'MM1',
            'code': 'MM1',
            'location_type': 'micro_market',
            'partner_id': self.customer1}]).id
        self.mm2 = self.env['stock.warehouse'].create([{
            'name': 'MM2',
            'code': 'MM2',
            'location_type': 'micro_market',
            'partner_id': self.customer2}]).id
        self.mm3 = self.env['stock.warehouse'].create([{
            'name': 'MM3',
            'code': 'MM3',
            'location_type': 'micro_market',
            'partner_id': self.customer1}]).id

    def test_create_employee_discount(self):
        """Test sequence generation on create"""
        # Create without sequence
        discount1 = self.employee_discount.create([{
            'discount': 10,
            'micro_market_ids': [self.mm1]}])
        self.assertNotEqual(discount1.sequence, 'New')
        # Create with existing sequence
        discount2 = self.employee_discount.create([{
            'sequence': 'CUSTOM123',
            'discount': 20,
            'micro_market_ids': [self.mm2]}])
        self.assertEqual(discount2.sequence, 'CUSTOM123')

    def test_discount_constraints(self):
        """Test discount percentage validation"""
        # Valid discount
        valid = self.employee_discount.create([{
            'discount': 50,
            'micro_market_ids': [self.mm2]}])

        # Test invalid discounts
        with self.assertRaises(UserError):
            self.employee_discount.create([{
                'discount': 101,
                'micro_market_ids': [self.mm1]}])

        with self.assertRaises(UserError):
            self.employee_discount.create([{
                'discount': 0,
                'micro_market_ids': [self.mm2]}])

        with self.assertRaises(UserError):
            self.employee_discount.create([{
                'discount': -5,
                'micro_market_ids': [self.mm2]}])

    def test_compute_partner_ids(self):
        """Test computation of partner_ids"""
        # Create test partners
        partner1 = self.env['res.partner'].create([{
            'name': 'Partner 1',
            'zip': 90703,
            'total_mm': 5}])
        partner2 = self.env['res.partner'].create([{
            'name': 'Partner 2',
            'zip': 12345,
            'total_mm': 0}])
        mm3 = self.env['stock.warehouse'].create([{
            'name': 'MM3',
            'code': 'MM3',
            'location_type': 'micro_market',
            'partner_id': partner1.id}]).id
        discount = self.employee_discount.create([{
            'discount': 10,
            'sequence': 'TEST123',
            'micro_market_ids': [mm3]}])
        self.assertIn(partner1, discount.partner_ids)
        self.assertNotIn(partner2, discount.partner_ids)

    def test_compute_market_dom_ids(self):
        """Test market_dom_ids computation"""
        desk = self.employee_discount.create([{
            'discount': 10,
            'customer_ids': [(6, 0, [self.customer1])],
            'micro_market_ids': [(6, 0, [self.mm1])]
        }])
        desk._compute_market_dom_ids()
        # Should return partner's markets except the assigned one
        self.assertIn(self.mm3, desk.market_dom_ids.ids)
        self.assertNotIn(self.mm1, desk.market_dom_ids.ids)
        self.assertNotIn(self.mm2, desk.market_dom_ids.ids)

    def test_onchange_user_line(self):
        """Test user_ids update based on user_line changes"""
        user1 = self.env['res.app.users'].create([{
            'name': 'User 1',
            'email': 'user1@gmail.com'}])
        user2 = self.env['res.app.users'].create([{
            'name': 'User 2',
            'email': 'user2@gmail.com'}])
        discount = self.employee_discount.create([{
            'discount': 10,
            'micro_market_ids': [self.mm1],
            'user_line': [(0, 0, {
                'first_name': 'User',
                'last_name': '1',
                'email': 'user1@gmail.com',
                'disable_user': False
            })] }])
        # Test adding user
        discount.write({
            'user_line': [(0, 0, {
                'first_name': 'User',
                'last_name': '2',
                'email': 'user2@gmail.com',
                'disable_user': False
            })]})
        self.assertIn(user2.id, discount.user_ids.ids)
        # Test disabling user
        discount.user_line[0].disable_user = True
        discount._onchange_user_line()
        self.assertNotIn(user1.id, discount.user_ids.ids)

    def test_action_confirm_desk(self):
        """Test state change to done"""
        discount = self.employee_discount.create([{
            'discount': 10,
            'micro_market_ids': [self.mm1],
            'state': 'draft'
        }])
        discount.action_confirm_desk()
        self.assertEqual(discount.state, 'done')
