# -*- coding: utf-8 -*-
import hashlib
from odoo import http
from odoo.http import _logger, request

class UserSignup(http.Controller):

    @http.route('/Averigo/RestApi/User_Registration_V1', type='json', auth='public', method=['POST'])
    def user_sign_up(self):
        try:
            data = request.get_json_data()

            # Check all required fields are present
            required_fields = ['FIRSTNAME', 'LASTNAME', 'EMAIL_ID', 'PASSWORD', 'PHONE_NO']
            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return {"Status": "Failure", "Message": f"Missing fields: {', '.join(missing_fields)}"}

            # Search for users by email and phone
            email_registered = request.env['res.app.users'].with_context(active_test=False).sudo().search([('email', '=', data['EMAIL_ID'])])
            phone_registered = request.env['res.app.users'].with_context(active_test=False).sudo().search([('phone', '=', data['PHONE_NO'])])

            # Check if email or phone is registered but inactive
            if (email_registered and (len(email_registered) > 1 or not email_registered.active)) or (phone_registered and (len(phone_registered) > 1 or not phone_registered.active)):
                return {"Status": "Error", "Message": "Email ID or Mobile Number already registered"}

            # Validate process status and incomplete registration
            if data['PROCESS_STATUS'] == 'IN' and not email_registered and not phone_registered:
                if 'VersionName' not in data or ('VersionName' in data and data['VersionName'] < '2.5'):
                    return {
                        "Status": "Failure",
                        "Message": "SignUp failed. You are using an old GrabScanGo version. Please upgrade the app and try again"
                    }

                fields = request.env['ir.model.fields'].sudo().search([('model', '=', 'res.app.users')]).mapped('name')
                values = {}
                for key, value in data.items():
                    if key == 'FIRSTNAME':
                        values['name'] = f"{data['FIRSTNAME']} {data['LASTNAME']}"
                    elif key.lower() in fields:
                        values[key.lower()] = data[key]
                    elif key == 'EMAIL_ID':
                        values['email'] = value
                    elif key == 'PHONE_NO':
                        values['phone'] = value
                    elif key == 'ADDRESS':
                        values['street'] = value
                    elif key == 'STATE':
                        values['state_id'] = request.env['res.country.state'].search([('name', '=', value)]).id
                    elif key == 'COUNTRY':
                        values['country_id'] = request.env['res.country'].search([('code', '=', value)]).id

                values['end_user'] = True

                # Encrypt password using SHA-1
                values['password'] = hashlib.sha1(data['PASSWORD'].encode()).hexdigest()

                request.env['res.app.users'].sudo().create(values)
                return {"Status": "Success", "Message": "Signup Successful."}

            elif data['PROCESS_STATUS'] == 'UP' and email_registered and phone_registered:
                # Encrypt new password using SHA-1
                updated_password = hashlib.sha1(data['PASSWORD'].encode()).hexdigest()
                request.env['res.app.users'].sudo().search([('id', '=', email_registered.id)]).write({'password': updated_password})
                return {"Status": "Success", "Message": "Password Changed Successfully."}

            else:
                return {"Status": "Error", "Message": "Email ID or Mobile Number already registered."}

        except Exception as e:
            _logger.exception("Signup Failed")
            return {
                "Status": "Failure",
                "Message": "Signup Failed due to an unexpected error. Please try again later."
            }
