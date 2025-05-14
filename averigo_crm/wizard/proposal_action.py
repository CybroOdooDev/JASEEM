# -*- coding: utf-8 -*-
from odoo import models, fields


class ProposalActionWizard(models.TransientModel):
    """ Proposal Wizard """
    _name = "proposal.action.wizard"
    _description = "Proposal Action Wizard"

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    crm = fields.Many2one('crm.lead')
    date = fields.Datetime('Date', default=fields.Datetime.now)

    def action_accept(self):
        """ Move to Proposal State"""
        active_id = self.env.context.get('active_id')
        self.crm = active_id
        self.crm.stage_id = self.env.ref('averigo_crm.stage_lead03').id

