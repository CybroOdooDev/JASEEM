# -*- coding: utf-8 -*-
import json
import hashlib
from odoo import http
from odoo.http import request, Response

class UserSignin(http.Controller):

    @http.route('/Averigo/RestApi/User_SignIn_V2', type='http', auth='public', methods=['POST'], csrf=False)
    def user_sign_in(self, **kwargs):
        try:
            login = kwargs.get('EmailID')
            password = kwargs.get('Password')

            if not login or not password:
                return Response(json.dumps({"Status": "Failure", "Message": "Missing login or password"}),
                                headers={'content-type': 'application/json'})

            # Authenticate User
            user = request.env['res.app.users'].sudo().with_context(active_test=False).search([('email', '=', login)], limit=1)

            if not user:
                return Response(json.dumps({"Status": "Failure", "Message": "Invalid credentials"}),
                                headers={'content-type': 'application/json'})

            if not user.active:
                return Response(json.dumps({"Status": "Error", "Message": "Unauthorized user. Please contact support."}),
                                headers={'content-type': 'application/json'})

            # Hash the input password using SHA-1 and compare with stored password
            hashed_password = hashlib.sha1(password.encode()).hexdigest()

            if user.password == hashed_password:
                token = request.env['jwt.manager'].sudo().generate_jwt_token(user.id)
                return Response(json.dumps({"Status": "Success", "Message": "Login successful", "token": token}),
                                headers={'content-type': 'application/json'})
            else:
                return Response(json.dumps({"Status": "Failure", "Message": "Invalid credentials"}),
                                headers={'content-type': 'application/json'})

        except Exception:
            return Response(json.dumps({"Status": "Failure", "Message": "Login Failed due to an unexpected error. Please try again later."}),
                            headers={'content-type': 'application/json'})
