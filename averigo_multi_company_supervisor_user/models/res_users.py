# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MultiCompanyUsers(models.Model):
    _inherit = 'res.users'

    is_supervisor = fields.Boolean(string="Multi Company Supervisor", help="Boolean to identify Multi Company Supervisor users." )

    @api.model_create_multi
    def create(self, vals):
        """ Super the create function to check and add the details for Multi-Company Supervisor users."""
        for val in vals:
            if val.get('is_supervisor'):
                val['email'] = val.get('login')
                val['company_id'] = 1
        return super(MultiCompanyUsers, self).create(vals)
