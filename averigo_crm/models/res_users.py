# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsersCrm(models.Model):
    _inherit = 'res.users'

    group_crm_operator = fields.Boolean(string="CRM", default=False)

    @api.model
    def create(self, vals_list):
        """ inherits create function to add crm access"""
        res = super(ResUsersCrm, self).create(vals_list)
        if 'create_company' in self._context and self._context[
            'create_company']:
            # add operator access rights
            res.group_crm_operator = True
            res._add_one_access_right('averigo_crm.operator_crm')
        return res
