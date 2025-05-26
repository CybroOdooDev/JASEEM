# -*- coding: utf-8 -*-

import base64
import os
import requests
from docusign_esign import ApiClient, ApiException, EnvelopeDefinition, \
    Document, Recipients
from docusign_esign import EnvelopesApi
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError

# root_path = '/home/ubuntu/docusign_files'
root_path = '.'


def action_login_docusign(user_id, account_id, integratorKey, privatekey):
    """ To connect docusign"""
    api_client = ApiClient()
    api_client.host = 'https://demo.docusign.net/restapi'

    SCOPES = ["signature"]
    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")
        envelope_api = EnvelopesApi(api_client)

        from_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        results = envelope_api.list_status_changes(
            account_id=account_id,
            from_date=from_date)
        headers = {'Authorization': f"Bearer {access_token.access_token}",
                   'Accept': 'application/json'}
        url = 'https://account-d.docusign.com/restapi/v2.1/accounts/' + account_id + '/brands'
        response = requests.get(url=url, headers=headers)
        status = response.status_code
        return status
    except ApiException as err:
        print(err, 'err')


def action_send_docusign_file(user_id, account_id, integratorKey, privatekey, filename,
                       fileContents, receiver_name, receiver_email, tabs1):
    """ Fun to send document through docusign"""
    signers_list = []
    print(len(receiver_email))
    for i in range(0, len(receiver_email)):
        # a = tabs1[i]['signHereTabs']
        # for d in a:
        #     d['yPosition'] -= 30
        signer = {'email': receiver_email[i], 'name': receiver_name[i],
                  'recipientId': i + 1, 'tabs': tabs1[i]}
        signers_list.append(signer)
    print(signers_list)
    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)

    base64_file_content = fileContents.decode('ascii')

    # Create the document model
    document = Document(  # create the DocuSign document object
        document_base64=base64_file_content,
        name=filename,  # can be different from actual file name
        file_extension='pdf',  # many different document types are accepted
        document_id=1  # a label used to reference the doc
    )

    envelope_definition = EnvelopeDefinition(
        email_subject="Please sign this document",
        documents=[document],
        # The Recipients object wants arrays for each recipient type
        recipients=Recipients(signers=signers_list),
        status="sent")
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")

        response = envelope_api.create_envelope(
            account_id=account_id,
            envelope_definition=envelope_definition)
        status = 200
        envelope_id = response.envelope_id
        return envelope_id
    # append "/envelopes" to the baseUrl and use in the request
    except ApiException as err:
        print(err, 'err')


def get_status(integratorKey, envelopeId, privatekey, user_id, account_id):
    # Get Envelope Recipient Status
    # append "/envelopes/" + envelopeId + "/recipients" to baseUrl and use in the request
    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")

        results = envelope_api.get_envelope(
            account_id, envelopeId)
        return results.status
    except ApiException as err:
        print(err, 'err')


def download_documents(integratorKey, envelopeId, privatekey, user_id,
                           account_id):
    """ Function to download completed document"""
    doc_status = get_status(integratorKey, envelopeId, privatekey, user_id,
                            account_id)
    complete_path = ''

    if doc_status != 'completed':
        return doc_status, complete_path
    api_client = ApiClient()
    envelope_api = EnvelopesApi(api_client)
    api_client.host = 'https://demo.docusign.net/restapi'
    SCOPES = ["signature"]

    private_key = base64.b64decode(privatekey.datas)
    try:
        access_token = api_client.request_jwt_user_token(
            client_id=integratorKey,
            user_id=user_id,
            oauth_host_name="account-d.docusign.com",
            private_key_bytes=private_key,
            expires_in=3600,
            scopes=SCOPES
        )
        api_client.set_default_header(header_name="Authorization",
                                      header_value=f"Bearer {access_token.access_token}")
        documents = envelope_api.list_documents(
            account_id=account_id,
            envelope_id=envelopeId)
        temp_file = envelope_api.get_document(
            account_id=account_id,
            document_id=1,
            envelope_id=envelopeId)
        file = temp_file
        directory_path = os.path.join(root_path, "files")
        if not os.path.isdir(directory_path):
            try:
                os.mkdir(directory_path)
            except:
                raise ValidationError(
                    "Please provide access rights to module")

        attach_file_name = documents.envelope_documents[0].name
        file_path = os.path.join("files", attach_file_name)
        complete_path = os.path.join(root_path, file_path)
        with open(file, "rb") as input:

            # Creating "gfg output file.txt" as output
            # file in write mode
            with open(complete_path, "wb") as text_file:
                # Writing each line from input file to
                # output file using loop
                for line in input:
                    text_file.write(line)
                text_file.close()
        return doc_status, complete_path
    except ApiException as err:
        print(err, 'err')



