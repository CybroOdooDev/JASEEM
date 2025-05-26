# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SowActionWizard(models.TransientModel):
    """SOW Action Wizard for handling document workflows"""

    _name = "sow.action.wizard"
    _description = "SOW Wizard"

    # Fields
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
        """Toggle checkbox based on file attachment"""
        self.check = bool(self.file)
        if self.file:
            print(self.file_name)

    def action_accept(self):
        """Accept action - move to next stage or show popup"""
        if self.file:
            crm_id = self.crm
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead05').id
        else:
            return self._show_popup()

    def _show_popup(self):
        """Show SOW popup wizard"""
        view_id = self.env.ref('averigo_crm.sow_popup_wizard_view').id
        return {
            'name': _("Popup"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'sow.popup.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.model
    def get_json_data(self, res_id, tabs1):
        """Retrieve JSON data from document"""
        print(self.env.context)
        print("tabs1", tabs1)
        print("res_id", res_id)


    def send_sow(self):
        """Send SOW document via DocuSign"""
        if not self.data:
            raise UserError(
                'You need to add fields in the document! '
                'Double click the document to insert fields anywhere.'
            )

        active_id = self.env.context.get('active_id')
        crm_id = self.env['crm.lead'].browse(active_id)

        # Prepare email data
        receiver_email, receiver_name = [], []
        if not self.env.context.get('key') and self.email_ids:
            for email in self.email_ids:
                receiver_name.append(email.name)
                receiver_email.append(email.email)

        # Get DocuSign account
        account_id = self.env['docusign.credentials'].sudo().search([], limit=1)
        self.account_id = account_id

        # Prepare model info
        model_info = {
            'model_name': str(self._inherit),
            'id': self.id
        }

        # Send document
        self.env['docusign.send'].sudo().send_sow_documents(
            {}, receiver_name, receiver_email, self.file_name,
            self.file, account_id, model_info, self.data, active_id
        )

        # Update CRM
        crm_id.stage_id = self.env.ref('averigo_crm.stage_lead05').id
        crm_id.sow_indication_note = "SOW form sent successfully!"

        return {'type': 'ir.actions.client', 'tag': 'reload'}


class SowPopupWizard(models.TransientModel):
    """SOW Confirmation Popup Wizard"""

    _name = "sow.popup.wizard"
    _description = "SOW Popup"

    def action_continue(self):
        """Continue without SOW document"""
        active_id = self.env.context.get('active_id')
        sow_wizard = self.env['sow.action.wizard'].sudo().browse(active_id)
        crm_id = self.env['crm.lead'].sudo().browse(sow_wizard.crm)

        if crm_id.stage_id == self.env.ref('averigo_crm.stage_lead04'):
            crm_id.stage_id = self.env.ref('averigo_crm.stage_lead05').id
