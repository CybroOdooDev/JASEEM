# -*- coding: utf-8 -*-
import re
from odoo.addons.base.models.res_partner import _tz_get
from odoo import api, models, fields
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """
    Inherits the `res.company` model to add custom fields and functionality.

    This class extends the base `res.company` model to include additional fields such as
    legal name, operator domain, exact domain, and other company-related information.
    It also provides methods for validating email and phone numbers, computing domains,
    and handling address-related operations.
    """
    _inherit = 'res.company'
    _description = 'Operator'

    name = fields.Char(
        related='partner_id.name', string='Operator Name', required=True,
        store=True, readonly=False,
        help="The name of the company, related to the partner's name.")
    legal_name = fields.Char(
        string="Legal Name", help="The legal name of the company.")
    operator_domain = fields.Char(
        string="Operator Domain",
        help="The domain name associated with the operator.")
    exact_domain = fields.Char(
        string="Exact Domain", help="The full domain URL for the company.")
    is_main_company = fields.Boolean(
        string="Is Main Company", default=False,
        help="Indicates if the company is the main company.")
    base_domain = fields.Char(
        string="Base Domain", default='.averigo.com', readonly=True,
        help="The base domain suffix (e.g., '.averigo.com')")
    county = fields.Char(
        string="County", help="The county where the company is located.")
    support_email = fields.Char(
        string="Support Email",
        help="The support email address for the company.")
    favicon = fields.Binary(
        string="Company Favicon",
        help="This field holds the image used to display a favicon for a given company.")
    language = fields.Many2one(
        comodel_name='res.lang', string='Language', required=True,
        default=lambda self: self.env.ref("base.lang_en").id,
        help="The default language for the company.")
    decimal_precision = fields.Integer(
        string='Decimal Precision', default=2,
        help="The number of decimal places for numerical values.")
    date_format_selection = fields.Selection(
        selection=[('%m/%d/%Y', 'MM/DD/YYYY') , ('%d/%m/%Y', 'DD/MM/YYYY'),
                   ('%Y/%m/%d', 'YYYY/MM/DD')], string="Date Format",
        default='%m/%d/%Y',
        help="The date format used by the company.")
    time_format_selection = fields.Selection(
        selection=[('%H:%M', 'HH:MM'), ('%H:%M:%S', 'HH:MM:SS'),
                   ('%I:%M %p', 'HH:MM AM/PM'),
                   ('%I:%M:%S %p', 'HH:MM:SS AM/PM')],
        string="Time Format", default='%H:%M',
        help="The time format used by the company.")
    enable_item_code = fields.Boolean(
        string="Enable Product Code")
    default_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Default Warehouse")
    timezone = fields.Selection(
        string="Timezone", selection=_tz_get, default='PST8PDT')

    @api.onchange('email')
    def get_user_validation_email(self):
        """
        Validate the email address when it is changed.

        This method checks if the provided email address is valid using the `averigo_email_validation` method.
        If the email is invalid, it raises a validation error.

        Triggers:
            - When the `email` field is modified.
        """
        if self.email:
            self.averigo_email_validation(self.email)

    @api.onchange('phone')
    def get_user_validation_phone(self):
        """
        Validate the phone number when it is changed.

        This method checks if the provided phone number is valid using the `averigo_phone_validation` method.
        If the phone number is invalid, it raises a validation error.

        Triggers:
            - When the `phone` field is modified.
        """
        if self.phone:
            self.averigo_phone_validation(self.phone)

    @api.onchange('logo')
    def _onchange_operator_logo(self):
        """
        Copy the company logo to the favicon field.

        This method ensures that the company's favicon is updated whenever the logo is changed.

        Triggers:
            - When the `logo` field is modified.
        """
        if self.logo:
            self.favicon = self.logo

    @api.onchange('name', 'operator_domain')
    def _onchange_operator_name(self):
        """
        Compute the operator domain and exact domain based on the company name.

        This method generates the `operator_domain` and `exact_domain` fields based on the company name
        and the base URL configuration. It also handles cases where the base URL is an IP address.

        Triggers:
            - When the `name` or `operator_domain` fields are modified.
        """
        for rec in self:
            regex = r'''^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
                            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
                            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(
                            25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'''
            url_extension = ''
            temp_name = (rec.name.lower().replace(' ', '_')) if rec.name else ''
            temp_name = ''.join(e for e in temp_name if e.isalnum())
            if rec.operator_domain:
                temp_name = rec.operator_domain
            else:
                rec.operator_domain = temp_name
            rec.operator_domain = temp_name
            protocol = "http://"
            if rec.name:
                # check hosted with ip or proper domain and update domain
                base_url = (rec.env['ir.config_parameter'].sudo().get_param(
                    'web.base.url')).split("//")
                protocol = (base_url[0] if base_url else "http:") + "//"
                base_url = base_url[-1]
                # take 'averigo.com' if hosted with ip
                if re.search(regex, base_url):
                    url_extension = ".averigo.com"
                else:
                    base_url = base_url.split(":")[0]
                    base_url = base_url.split(".")
                    if len(base_url) > 2:
                        url_extension = "." + str(base_url[-2]) + "." + str(
                            base_url[-1])
                    else:
                        url_extension = '.' + '.'.join(base_url) \
                            if len(base_url) > 1 else ".averigo.com"
            rec.base_domain = url_extension
            rec.exact_domain = protocol + rec.operator_domain + url_extension

    @api.onchange('zip')
    def get_address(self):
        """
        Fetch address details based on the ZIP code.

        This method retrieves the street, city, county, and state information based on the provided ZIP code.
        If the ZIP code is invalid, it raises a validation error.

        Triggers:
            - When the `zip` field is modified.
        """
        country = self.env.ref('base.us')
        if self.zip:
            zip_county_id = self.env['zip.county'].search(
                [('zip', '=', self.zip)], limit=1)
            self.street = zip_county_id.street or self.street
            if zip_county_id:
                self.county = zip_county_id.county or self.county
                self.city = zip_county_id.city or self.city
                if not self.state_id:
                    state_id = self.env['res.country.state'].search([
                        ('code', '=', zip_county_id.state),
                        ('country_id', '=', country.id)
                    ])
                    self.state_id = state_id.id if state_id else False
            else:
                raise ValidationError('Please enter a valid zip')
            self.zip = '{:0>5}'.format(self.zip)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to handle street and ZIP code updates.

        This method ensures that the street information is updated in the zip.county model
        when a new company is created. Additionally, it creates a default admin user for the company.

        Args:
            vals_list (list): A list of dictionaries containing the field values for the new records.

        Returns:
            res.company: The created company record(s).
        """
        # Create the company
        companies = super().create(vals_list)

        for company in companies:
            # Generate the username based on the company name
            username = f"{company.name.lower().replace(' ', '')}admin"[:64]  # Ensure username is not too long

            # Generate the email in the format: company_email@company_name
            if company.email:
                user_email = f"{company.email}@{company.name.lower().replace(' ', '')}"
            else:
                user_email = f"admin@{company.name.lower().replace(' ', '')}"

            # Check if a user with the same username or email already exists
            existing_user = self.env['res.users'].search([
                '|', ('login', '=', username), ('email', '=', user_email)
            ], limit=1)
            if existing_user:
                raise ValidationError("A user with the same username or email already exists.")

            # Create the default admin user
            user_vals = {
                'first_name': company.name,
                'last_name': 'Admin',
                'name': f"{company.name} Admin",
                'login': username,
                'email': company.email,
                'user_type': 'operator',
                'company_id': company.id,
                'company_ids': [(6, 0, [company.id])],
                'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
            }
            user = self.env['res.users'].create([user_vals])

            # Send a password reset email
            # user.action_reset_password()
        return companies

