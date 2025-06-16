# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    """Inheriting res_users model"""
    _inherit = 'res.users'

    user_type = fields.Selection(
        selection=[('admin', 'Admin'), ('operator', 'Operator'), ('customer', 'Customer')],
        string="User Type", default="admin")
    first_name = fields.Char(
        string="First Name")
    last_name = fields.Char(
        string="Last Name")

    @api.onchange('first_name', 'last_name')
    def _onchange_full_name(self):
        for record in self:
            record.name = f"{record.first_name or ''} {record.last_name or ''}".strip()

    @api.constrains('first_name', 'last_name')
    def _check_first_last_name(self):
        for rec in self:
            if not rec.first_name or not rec.first_name.strip():
                raise ValidationError(
                    _("First Name is required and cannot be empty."))
            if not rec.last_name or not rec.last_name.strip():
                raise ValidationError(
                    _("Last Name is required and cannot be empty."))


    _sql_constraints = [
        ('login_key', '1=1', 'You can not have two users with the same login !'),
    ]



