# -*- coding: utf-8 -*-

from odoo import fields, models


class CrmAdminUsers(models.Model):
    """ Class for configuring admin users in crm"""
    _name = 'crm.users.notify'
    _description = "Crm Admin Users"

    user_ids = fields.Many2many('res.users', string="Users")
    name = fields.Char(default="Admin users")
