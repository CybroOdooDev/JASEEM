# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SowActionWizard(models.TransientModel):
    """SOW Wizard"""
    _name = "sow.action.wizard"
    _description = "SOW Wizard"

    email_ids = fields.Many2many('additional.emails',
                                 string='Additional Emails')
    file = fields.Binary('Documents')
    file_name = fields.Char('Filename')
    account_id = fields.Many2one('docusign.credentials', 'DocuSign Account')
    crm = fields.Integer()
    data = fields.Json('data')
    check = fields.Boolean('checkbox')

    @api.onchange('file')
    def _onchange_check(self):
        """ To make check boolean field true or false"""
        if self.file:
            print(self.file_name)
            self.check = True
        else:
            self.check = False

    def action_accept(self):
        """ Open SOW popup if not documents attached"""
        if self.file:
            crm_id = self.crm
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead05').id
        else:
            view_id = self.env.ref(
                'averigo_crm.sow_popup_wizard_view').id
            return {
                'name': _("Popup"),
                # Name You want to display on wizard
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'sow.popup.wizard',
                # With . Example sale.order
                'type': 'ir.actions.act_window',
                'target': 'new',
            }

    def get_json_data(self, tabs1, res_id):
        """ to retrieve the json data from Document"""
        wiz = self.browse(res_id)
        wiz.data = tabs1

    def send_sow(self):
        """ To send SOW document"""
        if self.data:
            active_id = self.env.context.get('active_id')
            crm_id = self.env['crm.lead'].browse(active_id)
            receiver_email = []
            receiver_name = []
            if not self.env.context.get('key'):
                if self.email_ids:
                    for j in self.email_ids:
                        receiver_name.append(j.name)
                        receiver_email.append(j.email)
                attachment_ids = self.file
                file_name = self.file_name
                agreement = {}
            account_id = self.env['docusign.credentials'].sudo().search([],
                                                                        limit=1)
            self.account_id = account_id
            print(account_id)
            model_info = {}

            model_info['model_name'] = str(self._inherit)
            model_info['id'] = self.id
            self.env['docusign.send'].sudo().send_sow_documents(agreement,
                                                                receiver_name,
                                                                receiver_email,
                                                                file_name,
                                                                attachment_ids,
                                                                account_id,
                                                                model_info,
                                                                self.data,
                                                                active_id)
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead05').id
            crm_id.sow_indication_note = "Sow form sent successfully !"
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        else:
            raise UserError('You need to add fields in the document !!!!'
                            '  In the document displayed by double clicking you can insert fields anywhere in the document')


class SowPopupWizard(models.TransientModel):
    """SOW Popup"""
    _name = "sow.popup.wizard"
    _description = "SOW Popup"

    def action_continue(self):
        """ confirmation popup for moving to SOW without SOW document"""
        active_id = self.env.context.get('active_id')
        sow_wizard_id = self.env['sow.action.wizard'].sudo().browse(active_id)
        crm_id_sow = self.env['crm.lead'].sudo().browse(sow_wizard_id.crm)
        if crm_id_sow.stage_id == self.env.ref('averigo_crm.stage_lead04'):
            crm_id_sow.stage_id = self.env.ref('averigo_crm.stage_lead05').id
