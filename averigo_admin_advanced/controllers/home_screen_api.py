# -*- coding: utf-8 -*-
import json
from datetime import datetime
import pytz
from odoo import http
from odoo.http import request, _logger, Response


class ListNearbyMarkets(http.Controller):
    @http.route('/Averigo/RestApi/List_Nearby_Markets_V3',
                type='http', auth='public', method=['POST'], csrf=False)
    def list_nearby_markets(self, **kwargs):
        try:
            # Define timezone and get current time
            la_timezone = pytz.timezone('America/Los_Angeles')
            utc_time = datetime.now(pytz.utc)
            la_time = utc_time.astimezone(la_timezone)
            kwargs['DeviceDateTime'] = la_time.strftime('%Y-%m-%d %H:%M:%S')

            # Find the user
            user_id = None
            if kwargs.get('EmailID'):
                user_id = request.env['res.app.users'].sudo().search(
                    [('email', '=ilike', kwargs['EmailID'])], limit=1)

            headers = {'Content-Type': 'application/json'}
            base_url = request.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')

            if kwargs.get('BeaconMinor') == '':
                return Response(json.dumps({
                    "Status": "Error",
                    "Message": "No Micro Market List Found."
                }), headers=headers)

            lst = []
            featured_associated = {}
            beacon_ids = kwargs['BeaconMinor'].replace("'", "").split(",")

            for beacon_id_lst in beacon_ids:
                beacon_id = beacon_id_lst.split('-')
                beacon_major = beacon_id[0]
                beacon_minor = beacon_id[1]
                micro_market = request.env['stock.warehouse'].sudo().search([
                    ('beacon_major', '=', beacon_major),
                    ('beacon_minor', '=', beacon_minor)
                ])

                if micro_market:
                    to_email = request.env['res.mail.config'].sudo().search([
                        ('operator_id', '=', micro_market.company_id.id),
                        ('notification_type', '=', 'feedback')
                    ], limit=1, order='create_date desc')

                    send_to = ','.join(to_email.email_line_ids.mapped('email'))

                    front_desk = request.env['front.desk'].sudo().search([
                        ('micro_market_ids', 'in', [micro_market.id]),
                        ('user_ids', 'in', [user_id.id]),
                        ('desk_type', '=', 'front'),
                        ('state', '=', 'done')
                    ], limit=1)

                    user_line = request.env['front.desk.line'].sudo().search([
                        ('front_desk_id', '=', front_desk.id)
                    ])

                    employee = request.env['front.desk'].sudo().search([
                        ('micro_market_ids', 'in', [micro_market.id]),
                        ('user_ids', 'in', [user_id.id]),
                        ('desk_type', '=', 'employee'),
                        ('state', '=', 'done')
                    ], limit=1)

                    if not employee:
                        employee = request.env['employee.discount.setup'].sudo().search([
                            ('micro_market_ids', 'in', micro_market.id),
                            ('user_ids', 'in', user_id.id),
                            ('state', '=', 'done')
                        ], limit=1)

                    payroll_status = request.env['employee.credit.limit'].sudo().search([
                        ('app_user', '=', user_id.id),
                        ('payroll_id.micro_market_ids', 'in', [micro_market.id]),
                        ('payroll_id.disable_payroll', '=', False),
                        ('payroll_id.active', '=', True),
                        ('disable_user', '=', False)
                    ])

                    img = request.env['ir.image'].sudo().get_featured_image({
                        'time': kwargs['DeviceDateTime'],
                        'micro_market': micro_market.id,
                    })

                    payroll_type = "N"
                    credit_status = "N"
                    for status in payroll_status:
                        if status.payroll_id.deduction_type in ['credit', 'company']:
                            credit_status = "Y"
                        if status.payroll_id.deduction_type == 'payroll':
                            payroll_type = "Y"

                    user_type = "N"
                    if employee:
                        user_type = "E"
                    if front_desk and not user_line.disable_user:
                        # Credit and payroll not applicable for front desk user
                        user_type = "D"

                    specials = request.env['featured.products'].sudo().get_featured_product({
                        'time': kwargs['DeviceDateTime'],
                        'micro_market': micro_market.id
                    })

                    admin_featured = request.env['admin.featured.products'].sudo(). \
                        get_admin_featured_product({
                        'time': kwargs['DeviceDateTime'],
                        'micro_market': micro_market.id
                    })

                    special_banner = ""
                    admin_url = ""
                    admin_banner_text = ""
                    admin_image = ""

                    if front_desk or employee:
                        if img:
                            admin_banner_text = img['banner_text'] or ""
                            admin_image = img['image_url'] or ""

                    if not front_desk and not employee:
                        featured_associated = request.env['admin.featured.products'].sudo(). \
                            get_associated_product({
                            'time': kwargs['DeviceDateTime'],
                            'micro_market': micro_market.id
                        })

                        if admin_featured:
                            banner_id = [sub['ID'] for sub in admin_featured]
                            admin_featured_url = request.env['admin.featured.products']. \
                                sudo().search([('id', '=', max(banner_id))], limit=1)

                            admin_banner_text = admin_featured_url.banner_text
                            if admin_featured_url.banner_type == 'url':
                                admin_url = admin_featured_url.url
                            if admin_featured_url.banner_type == 'image':
                                admin_image = f"{base_url}/web/image_get?model=" \
                                              f"admin.featured.products&id=" \
                                              f"{admin_featured_url.image_update_count}-" \
                                              f"{admin_featured_url.id}&field=image"
                                admin_image = admin_image[0]

                        if specials:
                            res = [sub['ID'] for sub in specials]
                            banner_featured = request.env['featured.products'].sudo(). \
                                search([('id', '=', max(res))], limit=1)
                            special_banner = banner_featured.banner_text

                    out_side = ("Y" if any(micro_market.market_product_ids.mapped(
                        'categ_id').mapped('available_outside')) else "N")

                    values = {
                        "STATE_NAME": micro_market.state_id.name or "",
                        "CATEGORY_ID": "FEATURE" if len(
                            admin_featured) > 0 and user_type == 'N' else "",
                        "BANNER_IMAGE_NAME": "",
                        "DESK_TYPE": user_type,
                        "SALESTAX": str(micro_market.sales_tax) or '0.00',
                        "BEACONMAJOR": micro_market.beacon_major,
                        "BEACONMINOR": micro_market.beacon_minor,
                        "PRODUCT_RELATED_MAILID": send_to or "",
                        "BANNER_TEXT": admin_banner_text if admin_banner_text else "",
                        "PAYROLL_STATUS": payroll_type,
                        "LOCATION_ID": str(micro_market.id),
                        "BEACONVALUE": micro_market.beacon_major,
                        "PURCHASESTATUSFLAG": "Y",
                        "BANNER_IMAGE": admin_image if admin_image else "",
                        "LOC_ADD": micro_market.street if micro_market.street else "",
                        "PAY_USER_ID": str(
                            micro_market.company_id.id) if payroll_type == 'Y' else "",
                        "CREDIT_USER_ID": str(
                            micro_market.company_id.id) if credit_status == 'Y' else "",
                        "ISFEATURED": "Y" if len(
                            admin_featured) > 0 and user_type == 'N' else "N",
                        "DESK_USER_ID": str(
                            micro_market.company_id.id) if user_type == 'D' else "",
                        "APP_RELATED_MAILID": "support@grabscango.com",
                        "PRODUCT_RELATED_MAILID_LIST": send_to or "",
                        "CREDIT_STATUS": credit_status,
                        "LOCATION_DESC": micro_market.name,
                        "COMPANYNAME": micro_market.company_id.name,
                        "LOC_CITY": micro_market.city or "",
                        "SPL_BANNER_TEXT": special_banner if user_type == 'N' else "",
                        "SPL_CATEGORY_ID": "SPECIAL" if len(
                            specials) > 0 and user_type == 'N' else "",
                        "FEATURED_VIDEO_URL": admin_url,
                        "VIDEO_THUMBNAIL_URL": "",
                        "AD_IMAGE_LIST": [],
                        "AD_INTERVAL": 0,
                        "LAST_VISITED_MARKET": 'N',
                        "OUTSIDE_MARKET_CATEGORIES": out_side
                    }
                    values.update(featured_associated or {
                        "FEATURED_ITEM_NO": "",
                        "FEATURED_UPC": "",
                        "FEATURED_ITEM_NAME": ""
                    })
                    lst.append(values)

            if not lst or not user_id:
                return Response(
                    json.dumps({
                        "Status": "Error",
                        "Message": "No Micro Market List Found."
                    }),
                    headers=headers
                )
            else:
                return Response(
                    json.dumps({
                        "Status": 'Success',
                        "Micro Market List": lst
                    }),
                    headers=headers
                )

        except Exception as e:
            # Log the error with traceback
            _logger.exception(f"Error occurred while listing the nearby market - "
                              f"Error:-{str(e)}")
            return Response(
                json.dumps({
                    "Status": "Error",
                    "Message": "No Micro Market List Found."
                }),
                headers={'Content-Type': 'application/json'}
            )