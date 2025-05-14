# -*- coding: utf-8 -*-
from odoo import models, fields


class TransferLeadWizard(models.TransientModel):
    """Transfer Lead Wizard"""
    _name = "transfer.lead.wizard"
    _description = "Transfer Lead Wizard"

    company_id = fields.Many2one('res.company', string="Operator")

    def action_submit(self):
        """Fun to transfer lead"""
        active_id = self.env.context.get('active_id')
        crm_id = self.env['crm.lead'].browse(active_id)

        if self.company_id:
            rec_id = self.env['transfer.assign.users'].search(
                [('company_id', '=', self.company_id.id)])
            user_id = rec_id.user_id
            group_id = self.sudo().env.ref(
                'averigo_crm.operator_crm')
            group_id.users = user_id
            if crm_id:
                new = crm_id.with_user(1).copy({'type': 'opportunity',
                                                'parent_lead_id': crm_id.id,
                                                'company_id': self.company_id.id,
                                                'stage_id': crm_id.stage_id.id,
                                                'user_id': user_id.id,
                                                'is_activity_scheduled': crm_id.is_activity_scheduled,
                                                'partner_id': False,
                                                'email_from': False,
                                                'document': False,
                                                'attach_id': False,
                                                'indication_note': False,
                                                })
                base_url = self.company_id.exact_domain
                base_url += '/web#id=%d&view_type=form&model=%s' % (
                    new.id, new._name)
                new.lead_transfer_url = base_url
                template = self.env.ref(
                    'averigo_crm.message_lead_transfer')
                template.write({'email_to': self.company_id.email})
                template.sudo().send_mail(res_id=new.id, force_send=True)
