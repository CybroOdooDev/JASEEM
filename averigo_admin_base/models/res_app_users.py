# -*- coding: utf-8 -*-
import hashlib
import re

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class ResAppUsers(models.Model):
    """Represents application users in the system."""
    _name = 'res.app.users'
    _description = "App Users"
    _rec_name = "name"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name", required=True)
    active = fields.Boolean(
        'Active', default=True)
    email = fields.Char(
        string="Email", required=True)
    mobile = fields.Char(
        string="Mobile")
    zip = fields.Char()
    phone = fields.Char(
        string="Phone", size=120)
    street = fields.Char(
        string="Street")
    city = fields.Char(
        string="City")
    county = fields.Char()
    state_id = fields.Many2one(
        'res.country.state', string="Fed. State")
    country_id = fields.Many2one(
        'res.country', string="Country")
    end_user = fields.Boolean(
        default=False)
    code = fields.Char(
        string="Code")
    device_token = fields.Char(
        string="Device Token")
    last_session_id = fields.Many2one(
        'user.session.history', string="Last Session")
    last_session_date = fields.Datetime(string="Last Login")
    lastname = fields.Char(
        string='Last Name')
    device_udid = fields.Char(
        string='Device UDID')
    nickname = fields.Char(
        string='Nick Name')
    product_related_mailid = fields.Char(
        'Related EMail', help="Product related mail")
    enable_sms = fields.Selection(
        [('N', 'Y'), ('N', 'N')], string='Enable SMS', default="N")
    enable_newsletter = fields.Selection(
        [('Y', 'Yes'), ('N', 'No')], string='Enable Newsletter', default="N")
    password = fields.Char(
        string='Password')
    app_related_mail_id = fields.Char(
        'APP Related Email', help="app related mail id")
    item_reconcile = fields.Selection(
        [('Y', 'Y'), ('N', 'N')], string='Item Reconcile', default="N")
    usertype = fields.Selection(
        [('N', 'Normal User'), ('E', 'Employee')],
        string='Item Reconcile', default="N")
    service_name = fields.Char(
        string='Service Name')
    companyacro = fields.Char(
        string='Companyacro')
    admin_email_list = fields.Char(
        string='Admin Email List')
    company_name = fields.Char(
        string='Company Name')
    profile_image = fields.Boolean(
        string='Profile Image')
    item_receive = fields.Selection(
        [('Y', 'Y'), ('N', 'N')], string='Item Receive', default="N")
    item_add = fields.Selection(
        [('Y', 'Y'), ('N', 'N')], string='Add Item', default="N")
    otp = fields.Integer(
        string='OTP')
    password_reset_request = fields.Boolean(
        default=False)
    device_type = fields.Char(
        string='Device Type')
    last_visited = fields.Many2one(
        comodel_name='stock.warehouse')
    is_imported = fields.Boolean(
        string='Imported User')
    emp_code = fields.Char(
        string="Employee Ref. Code")
    employee_id = fields.Char(
        string='Employee id')

    def name_get(self):
        """Override the function to return name and email"""
        result = []
        for rec in self:
            result.append((rec.id, ("%s %s" % (
                rec.name, ("(%s)" % rec.email)) if rec.email else "")))
        return result

    def show_last_session_details(self):
        """Show session details"""
        tree_view_id = self.env.ref("base_averigo.user_session_history_tree")
        form_view_id = self.env.ref("base_averigo.user_session_history_form")
        return {
            'name': _('Session History'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
            'res_model': 'user.session.history',
            'domain': [('user_id', '=', self.id)],
            'target': 'new',
        }

    def reset_user_pwd_action(self):
        """Show password reset actions"""
        form_view_id = self.env.ref(
            "base_averigo.view_app_user_pwd_reset_form")
        ctx = {
            'default_app_user_id': self.id,
        }
        return {
            'name': _('Reset Password'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(form_view_id.id, 'form')],
            'res_model': 'app.user.pwd.reset',
            'context': ctx,
            'target': 'new',
        }

    @api.onchange('email')
    def onchange_user_email(self):
        """Email validation"""
        if self.email:
            self.averigo_email_validation(self.email)

    @api.onchange('password')
    def check_password(self):
        """ check password match """
        if self.password:
            self.password = hashlib.sha256(self.password.encode()).hexdigest()

    @api.constrains('email')
    def email_unique_check(self):
        """Validation for unique email"""
        for record in self:
            user = self.env['res.app.users'].sudo().search(
                [('email', '=ilike', record.email)], limit=1)
            if user.id and user.id != record.id:
                raise ValidationError(_(
                    "The email %s is already associated with another user" % record.email))

    @api.constrains('phone')
    def phone_unique_check(self):
        for record in self:
            if record.phone:
                if len(record.phone) != 10:
                    raise ValidationError(_("Enter 10 digit mobile number"))
                phone_registered = self.env['res.app.users'].sudo().search(
                    [('phone', 'ilike', record.phone)])
                if len(phone_registered) > 1:
                    raise ValidationError(_(
                        "The Phone %s is already associated with another user" % record.phone))


class AppUserPasswordReset(models.TransientModel):
    """Represents a transient model for resetting app user passwords."""
    _name = "app.user.pwd.reset"
    _description = "App User Password Reset"

    app_user_id = fields.Many2one(
        "res.app.users", string="App User")
    user_name = fields.Char(
        string="User Name", related="app_user_id.name")
    user_email = fields.Char(
        string="Email", related="app_user_id.email")
    new_password = fields.Char(
        string="New Password")
    confirm_pwd = fields.Char(
        string="Confirm Password")
    check_match = fields.Boolean()

    @api.onchange('new_password', 'confirm_pwd')
    def check_password(self):
        """To check password match"""
        if self.new_password and self.confirm_pwd and \
                self.new_password != self.confirm_pwd:
            self.check_match = False
        else:
            self.check_match = True

    def change_password(self):
        """Function for change user password"""
        if self.app_user_id and self.new_password and self.confirm_pwd:
            if self.new_password != self.confirm_pwd:
                raise UserError(
                    _("Passwords does not match. Please try again..!"))
            self.app_user_id.password = hashlib.sha256(
                self.new_password.encode()).hexdigest()
