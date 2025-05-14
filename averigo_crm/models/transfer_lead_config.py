# -*- coding: utf-8 -*-
from odoo import fields, models, api


class TransferLeadUsers(models.Model):
    """Transfer Lead Users"""
    _name = 'transfer.lead.users'
    _description = "Transfer Lead Users"

    name = fields.Char(default="Transfer Access users")
    transfer_user_ids = fields.One2many('transfer.access.users',
                                        'user_details_id', invisible=True,
                                        store=True)

    def write(self, vals):
        """ to add users to lead transfer group"""
        res = super(TransferLeadUsers, self).write(vals)
        if 'transfer_user_ids' in vals:
            users = self.transfer_user_ids.user_ids
            group_id = self.sudo().env.ref('averigo_crm.group_lead_transfer_user')
            group_id.users = False
            for user in users:
                group_id.users += user
        return res


class TransferAccessUsers(models.Model):
    """Transfer Access Users"""
    _name = 'transfer.access.users'
    _description = "Transfer Access Users"

    user_details_id = fields.Many2one('transfer.lead.users')
    company_id = fields.Many2one('res.company', string='Operator')
    user_ids = fields.Many2many('res.users', string='Users')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """ To return users based on company"""
        return {
            'domain': {'user_ids': [('company_id', '=', self.company_id.id)]}}


class DefaultLeadAssignUsers(models.Model):
    """Default Lead Assign"""
    _name = 'default.lead.assign.users'
    _description = "Default Lead Assign"

    name = fields.Char(default="Default Lead Assign users")
    default_user_ids = fields.One2many('transfer.assign.users',
                                       'user_details_id', invisible=True,
                                       store=True)


class TransferAssignUsers(models.Model):
    """Transfer Assign Users"""
    _name = 'transfer.assign.users'
    _description = "Transfer Assign Users"

    user_details_id = fields.Many2one('default.lead.assign.users')
    company_id = fields.Many2one('res.company', string='Operator')
    user_id = fields.Many2one('res.users', string='Users')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """ To return users based on company"""
        return {
            'domain': {'user_id': [('company_id', '=', self.company_id.id)]}}
