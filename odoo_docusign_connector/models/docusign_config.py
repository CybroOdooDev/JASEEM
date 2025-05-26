# -*- coding: utf-8 -*-

import base64
import os
import shutil
from . import docusign
from odoo import models, fields
from odoo.exceptions import UserError, ValidationError


class DocusignCredentials(models.Model):
    """ To setup the Docusign account credentials for integrating with odoo"""
    _name = 'docusign.credentials'
    _description = "Docusign Credentials Setup"

    name = fields.Char(string="Name", required=True, help="Name of record")
    user_email = fields.Char(string="Email", required=True,
                             help="Docusign user email address")
    user_password = fields.Char(string="Password", required=True,
                                help="Docusign user password")
    integrator_key = fields.Char(string="Docusign Integrator Key",
                                 required=True, help="Docusign Integrator key")
    account_id_data = fields.Char(string='Docusign Account Id', required=True,
                                  help="Docusign user account ID")
    user_id_data = fields.Char(string='Docusign User Id', required=True,
                               help="Docusign user ID")
    private_key_ids = fields.Many2many('ir.attachment',
                                       string='Private Key File',
                                       required=True,
                                       help="Private key attachment")
    company_id = fields.Many2one('res.company', string="Operator",
                                 default=lambda self: self.env.user.company_id,
                                 help="company ID",
                                 context={'user_preference': True})

    def action_test_credentials(self):
        """ Function to test whether the credentials are valid or not"""
        status = docusign.action_login_docusign(self.user_id_data, self.account_id_data,
                                                self.integrator_key,
                                                self.private_key_ids)
        if status != 200:
            raise UserError("Connection Failed!")
        else:
            raise UserError(" Connection Successful !")


class SendDocument(models.Model):
    """To send the Document and acquire status of document"""
    _name = "docusign.send"
    _description = "Docusign Send Documents"

    def action_send_documents(self, agreement_rec, receiver_name, receiver_email, file_name,
                       attachment_ids, account_id, model_info, tabs1, active_id):
        """ function to send the document """
        crm_id = self.env['crm.lead'].browse(active_id)
        user = account_id
        docusign_email = user.user_email
        docusign_pwd = user.user_password
        docusign_auth_key = user.integrator_key
        docusign_user_id = user.user_id_data
        docusign_account_id = user.account_id_data
        docusign_private_key = user.private_key_ids

        if not receiver_email:
            raise ValidationError('Recipient email has not been defined')

        if not attachment_ids:
            raise ValidationError('Attachments not found')

        if not docusign_email or not docusign_pwd or not docusign_auth_key:
            raise ValidationError(
                'Connection Failed! Docusign credentials are missing.')
        file_name = file_name
        file_data_encoded_string = attachment_ids
        envelop_id = docusign.action_send_docusign_file(docusign_user_id,
                                                        docusign_account_id,
                                                        docusign_auth_key,
                                                        docusign_private_key,
                                                        file_name,
                                                        file_data_encoded_string,
                                                        receiver_name,
                                                        receiver_email,
                                                        tabs1)

        crm_id.document = envelop_id
        self.env.cr.commit()

    def document_status(self, documents, model_info):
        """ function to get the status of document sent"""
        for document in documents:
            user = document.account_id
            docusign_email = user.user_email
            docusign_pwd = user.user_password
            docusign_auth_key = user.integrator_key
            docusign_user_id = user.user_id_data
            docusign_account_id = user.account_id_data
            docusign_private_key = user.private_key_ids
            envelope_id = document.document
            if not docusign_email or not docusign_pwd or not docusign_auth_key:
                raise ValidationError(
                    'Connection Failed! Docusign credentials are missing.')

            if envelope_id:
                docu_status, complete_path = docusign.download_documents \
                    (docusign_auth_key,
                     envelope_id, docusign_private_key, docusign_user_id,
                     docusign_account_id)
                document.complete_document = docu_status
                if complete_path != '':
                    path_split = complete_path.rsplit('/', 1)
                    attach_file_name = path_split[1]
                    folder_path = path_split[0]
                    with open(complete_path, "rb") as open_file:
                        encoded_string = base64.b64encode(
                            open_file.read())
                    values = {'name': attach_file_name,
                              'type': 'binary',
                              'res_id': self.id,
                              'res_model': 'crm.lead',
                              'datas': encoded_string,
                              'index_content': 'image',
                              'store_fname': attach_file_name,
                              }
                    attach_id = self.env['ir.attachment'].create(values)
                    document.attach_id = attach_id

                    os.remove(complete_path)
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                self.env.cr.commit()
            else:
                raise UserError('No agreement documents are sent')

    def send_sow_documents(self, agreement_rec, receiver_name, receiver_email, file_name,
                           attachment_ids, account_id, model_info, tabs1,
                           active_id):
        """ function to send sow document"""
        crm_id = self.env['crm.lead'].browse(active_id)
        user = account_id
        docusign_email = user.user_email
        docusign_pwd = user.user_password
        docusign_auth_key = user.integrator_key
        docusign_user_id = user.user_id_data
        docusign_account_id = user.account_id_data
        docusign_private_key = user.private_key_ids

        if not receiver_email:
            raise ValidationError('Recipient email has not been defined')

        if not attachment_ids:
            raise ValidationError('Attachments not found')

        if not docusign_email or not docusign_pwd or not docusign_auth_key:
            raise ValidationError(
                'Connection Failed! Docusign credentials are missing.')

        file_name = file_name
        file_data_encoded_string = attachment_ids
        envelop_id = docusign.action_send_docusign_file(docusign_user_id,
                                                            docusign_account_id,
                                                            docusign_auth_key,
                                                            docusign_private_key,
                                                            file_name,
                                                            file_data_encoded_string,
                                                            receiver_name,
                                                            receiver_email,
                                                            tabs1)
        crm_id.sow_document = envelop_id
        self.env.cr.commit()


