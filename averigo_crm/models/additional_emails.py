# -*- coding: utf-8 -*-

from odoo import fields, models


class AdditionalMails(models.Model):
    """ Model for storing additional emails"""
    _name = 'additional.emails'
    _description = "Additional Emails"

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email", required=True)