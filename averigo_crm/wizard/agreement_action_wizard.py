# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AgreementActionWizard(models.TransientModel):
    """ Wizard for agreement stage """
    _name = "agreement.action.wizard"
    _description = "Agreement Action Wizard"

    def _default_email_ids(self):
        """ To get partner email in crm model"""
        active_id = self.env.context.get('active_id')
        crm_id = self.env['crm.lead'].browse(active_id)
        emails = crm_id.partner_id
        return emails

    email_id = fields.Many2one('res.partner', string='Recipients',
                               default=_default_email_ids)
    additional_emails = fields.Many2many('additional.emails',
                                         string='Additional Emails')
    file = fields.Binary('Documents')
    file_name = fields.Char('Filename')
    account_id = fields.Many2one('docusign.credentials', 'DocuSign Account')
    crm = fields.Integer()
    data = fields.Json('data')
    check = fields.Boolean('checkbox')

    @api.onchange('file')
    def _onchange_check(self):
        """ To Make Boolean Field True or False Based On attachment added"""
        if self.file:
            self.check = True
        else:
            self.check = False

    @api.model
    def get_json_data(self, res_id, tabs1):
        """ To retrieve json from Agreement PDF"""

        print("*********",tabs1)
        wiz = self.browse(res_id)

        wiz.data = tabs1

    def send_documents(self):
        """ To Send agreement Doc and move to agreement stage"""
        if self.data:
            active_id = self.env.context.get('active_id')
            crm_id = self.env['crm.lead'].sudo().browse(active_id)
            receiver_email = []
            receiver_name = []
            if not self.env.context.get('key'):
                if self.email_id:
                    for i in self.email_id:
                        receiver_name.append(i.name)
                        if i.email:
                            receiver_email.append(i.email)
                        else:
                            if crm_id.email_from:
                                receiver_email.append(crm_id.email_from)
                            else:
                                raise UserError(
                                    'Please add recepients email address')
                if self.additional_emails:
                    for j in self.additional_emails:
                        receiver_name.append(j.name)
                        receiver_email.append(j.email)
                attachment_ids = self.file
                file_name = self.file_name
                agreement = {}

            account_id = self.env['docusign.credentials'].sudo().search([],
                                                                        limit=1)
            self.account_id = account_id
            model_info = {}
            model_info['model_name'] = str(self._inherit)
            model_info['id'] = self.id
            self.env['docusign.send'].sudo().action_send_documents(agreement,
                                                                   receiver_name,
                                                                   receiver_email,
                                                                   file_name,
                                                                   attachment_ids,
                                                                   account_id,
                                                                   model_info,
                                                                   self.data,
                                                                   active_id)
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead04').id
            crm_id.indication_note = "Document sent successfully !"
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise UserError('You need to add fields in the document !!!!'
                            '   In the document displayed, by double clicking you can insert fields anywhere in the document')

    def action_accept(self):
        """ Return Agreement Popup Wizard"""
        active_id = self.env.context.get('active_id')
        if self.file:
            crm_id = self.env['crm.lead'].browse(active_id)
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead04').id
        else:
            view_id = self.env.ref(
                'averigo_crm.agreement_popup_wizard_view').id
            return {
                'name': _("Popup"),
                # Name You want to display on wizard
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'agreement.popup.wizard',
                # With . Example sale.order
                'type': 'ir.actions.act_window',
                'target': 'new',
            }


class AgreementPopupWizard(models.TransientModel):
    _name = "agreement.popup.wizard"
    _description = "Agreement Popup"

    def action_continue(self):
        """ Move to Agreement Stage"""
        active_id = self.env.context.get('active_id')
        wizard_id = self.env['agreement.action.wizard'].sudo().browse(active_id)
        crm_id = self.env['crm.lead'].sudo().browse(wizard_id.crm)
        if crm_id.stage_id == self.env.ref('averigo_crm.stage_lead03'):
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead04').id
