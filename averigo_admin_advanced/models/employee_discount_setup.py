# -*- coding: utf-8 -*-
import binascii
import chardet
import csv
import io
import base64
import openpyxl

from odoo import models, fields, api, _
from odoo.api import _logger
from odoo.exceptions import UserError


class EmployeeDiscountSetup(models.Model):
    """Represents the setup for employee discounts at the admin level."""
    _name = "employee.discount.setup"
    _description = "Employee Discount Admin Level"
    _rec_name = 'sequence'
    _order = 'create_date desc'

    sequence = fields.Char(
        string="Employee Discount Id", copy=False, default='New', readonly=True)
    active = fields.Boolean(
        string="Active", default=True)
    micro_market_ids = fields.Many2many(
        comodel_name='stock.warehouse', string="MicroMarket",
        domain=[('location_type', '=', 'micro_market')], ondelete='restrict')
    market_dom_ids = fields.Many2many(
        'stock.warehouse', string="Market Domain",
        compute='_compute_market_dom_ids')
    customer_ids = fields.Many2many(
        'res.partner', string="Bill To Customer")
    partner_ids = fields.Many2many(
        'res.partner', compute='_compute_partner_ids')
    user_ids = fields.Many2many(
        'res.app.users', string="App Users")
    discount = fields.Float(
        string="Discount")
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Confirmed')], string="Status",
        default='draft')
    company_id = fields.Many2one(
        'res.company', string="Operator",
        default=lambda self: self.env.user.company_id)
    user_line = fields.One2many(
        'employee.discount.line', 'emp_discount_id',
        string="User List", copy=False)
    import_file = fields.Binary(
        string='File', required=True)
    file_name = fields.Char()
    extension = fields.Char()
    add_existing = fields.Selection(
        [('link', 'Link It'), ('skip', 'Skip It'), ('error', 'Let me know')],
        string="If Found Duplicates", default='link')

    @api.model_create_multi
    def create(self, vals_list):
        """Automatically generate a sequence number for employee discount."""
        ref = self.env.ref('averigo_admin_advanced.employee_discount_sequence')
        for vals in vals_list:
            if vals.get('sequence', _('New')) == _('New'):
                vals['sequence'] = ref.with_company(self.env.user.company_id.id).next_by_code(
                    "employee.discount.setup") or _('New')
        return super(EmployeeDiscountSetup, self).create(vals_list)

    @api.constrains('discount')
    def _check_discount(self):
        """Ensures the discount percentage is within the valid range"""
        if self.discount <= 0 or self.discount > 100:
            raise UserError(_("Percentage should be between 0% to 100%!"))

    @api.onchange('micro_market_ids')
    def _onchange_micro_market_ids(self):
        """Ensure all selected micro markets belong to the same partner"""
        if not self.micro_market_ids:
            return
        partners = self.micro_market_ids.mapped('partner_id')
        self.customer_ids = partners.ids

    @api.depends('customer_ids', 'micro_market_ids')
    def _compute_market_dom_ids(self):
        """Changes the domain of micro markets based on the selected customers."""
        for market in self:
            if market.customer_ids:
                all_markets = self.env['stock.warehouse'].search([
                    ('location_type', '=', 'micro_market'),
                    ('partner_id', 'in', market.customer_ids.ids)
                ])
                assigned_ids = []
                for m in market.micro_market_ids:
                    if m._origin:  # If it's a NewId, get the original ID
                        assigned_ids.append(m._origin.id)
                    else:  # Normal saved record
                        assigned_ids.append(m.id)
                # Filter out assigned markets
                available_markets = all_markets.filtered(
                    lambda m: m.id not in assigned_ids)
                market.market_dom_ids = available_markets
            else:
                all_markets = self.env['stock.warehouse'].search([
                    ('location_type', '=', 'micro_market')])
                assigned_ids = []
                for m in market.micro_market_ids:
                    if m._origin:  # If it's a NewId, get the original ID
                        assigned_ids.append(m._origin.id)
                    else:  # Normal saved record
                        assigned_ids.append(m.id)
                # Filter out assigned markets
                available_markets = all_markets.filtered(
                    lambda m: m.id not in assigned_ids)
                market.market_dom_ids = available_markets

    @api.depends('sequence', 'customer_ids')
    def _compute_partner_ids(self):
        """Compute partner IDs based on micromarkets associated with partners"""
        for partner in self:
            partner_ids = self.env['res.partner'].search([]).filtered(
                lambda s: s.total_mm != 0)
            associated_ids = set()
            for customer in partner.customer_ids:
                if customer._origin:
                    associated_ids.add(customer._origin.id)
                else:
                    associated_ids.add(customer.id)
            available_partners = partner_ids.filtered(
                lambda p: p.id not in associated_ids)
            partner.partner_ids = available_partners

    @api.onchange('user_line')
    def _onchange_user_line(self):
        """Updates the user_ids field based on changes in the user_line field."""
        for record in self.user_line:
            if record._origin.id and record.disable_user:
                self.write(
                    {"user_ids": [(fields.Command.unlink(record.app_user.id))]})
            elif record._origin.id:
                self.write(
                    {"user_ids": [(fields.Command.link(record.app_user.id))]})

    def action_confirm_desk(self):
        """Confirms the employee discount setup from draft to done state."""
        self.state = 'done'

    #
    def file_import(self):
        """Opens a form to import users."""
        self.import_file = False
        return {
            'name': _('Import Users'),
            'type': 'ir.actions.act_window',
            'res_model': 'employee.discount.setup',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref(
                'averigo_admin_advanced.app_user_import_employee_discount_form').id
        }

    @api.onchange('import_file')
    def _onchange_import_file(self):
        """Updates the file extension when the import_file field changes."""
        if self.file_name:
            self.extension = self.file_name.split('.')[-1]
        else:
            self.extension = False

    def upload_file(self):
        """To Upload file for importing app users"""
        necessary_columns = {'first name', 'last name', 'email', 'phone',
                             'employee id'}
        self.env.cr.execute("SELECT email FROM res_app_users")
        existing_emails = {email[0].lower() for email in self.env.cr.fetchall()}
        if self.extension in ['xlsx', 'xls']:
            try:
                file_data = binascii.a2b_base64(self.import_file)
                workbook = openpyxl.load_workbook(io.BytesIO(file_data),
                                                  data_only=True)
                sheet = workbook.active
                headers = {cell.value.lower(): idx for idx, cell in
                           enumerate(sheet[1]) if
                           cell.value and cell.value.lower() in necessary_columns}
                if 'email' not in headers:
                    raise UserError("Missing required column: 'email'")
                vals_list, existing_users = [], []
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    vals = {key.replace(" ", "_"): row[idx] for key, idx in
                            headers.items()}
                    email_lower = vals['email'].lower()

                    if email_lower in existing_emails:
                        if self.add_existing == 'link':
                            user = self.env['res.app.users'].sudo().search(
                                [('email', '=ilike', vals['email'])], limit=1)
                            user.employee_id = str(
                                vals['employee_id']) if vals.get(
                                'employee_id') else ''
                            existing_users.append(user.id)
                        elif self.add_existing == 'skip':
                            continue
                        else:
                            raise UserError(
                                f"User with email {vals['email']} already exists")
                    else:
                        vals.update({
                            'name': f"{vals['first_name']} {vals['last_name']}",
                            'is_imported': True,
                            'employee_id': str(vals.get('employee_id', ''))
                        })
                        vals.pop('first_name', None)
                        vals.pop('last_name', None)
                        vals_list.append(vals)
                users = [self.env['res.app.users'].create(va).id for va in
                         vals_list]
                users.extend(existing_users)
                for user in self.env['res.app.users'].browse(users):
                    if user not in self.user_line.app_user:
                        self.user_line.create({
                            'first_name': user.name.split(' ', 1)[0],
                            'last_name': user.name.split(' ', 1)[
                                1] if ' ' in user.name else user.lastname or " ",
                            'email': user.email,
                            'app_user': user.id,
                            'employee_id': str(user.employee_id) or '',
                            'emp_discount_id': self.id
                        })
                        self.write({"user_ids": [(4, user.id)]})
            except Exception as e:
                _logger.error(str(e))
                raise UserError("Invalid File..!")
            finally:
                self.import_file = None

        elif self.extension == 'csv':
            try:
                csv_data = base64.b64decode(self.import_file)
                # Detect encoding
                detected_encoding = chardet.detect(csv_data)['encoding']
                detected_encoding = detected_encoding if detected_encoding else "utf-8"
                # Decode using detected encoding
                data_file = io.StringIO(
                    csv_data.decode(detected_encoding, errors='replace'))
                reader = csv.reader(data_file)
                headers = next(reader)
                column_indices = {col.lower(): idx for idx, col in
                                  enumerate(headers) if
                                  col.lower() in necessary_columns}
                if 'email' not in column_indices:
                    raise UserError("Missing required column: 'email'")
                vals_list, existing_users = [], []
                for row in reader:
                    vals = {key.replace(" ", "_"): row[idx] for key, idx in
                            column_indices.items()}
                    email_lower = vals['email'].lower()
                    if email_lower in existing_emails:
                        if self.add_existing == 'link':
                            existing_users.append(
                                self.env['res.app.users'].search(
                                    [('email', '=ilike', vals['email'])],
                                    limit=1).id)
                        elif self.add_existing == 'skip':
                            continue
                        else:
                            raise UserError(
                                f"User with email {vals['email']} already exists")
                    else:
                        vals.update({
                            'name': f"{vals['first_name']} {vals['last_name']}",
                            'is_imported': True,
                            'lastname': vals.get('last_name', "")
                        })
                        vals.pop('first_name', None)
                        vals.pop('last_name', None)
                        vals_list.append(vals)

                users = [self.env['res.app.users'].create(va).id for va in
                         vals_list]
                users.extend(existing_users)
                for user in self.env['res.app.users'].browse(users):
                    if user.id not in self.user_line.app_user.ids:
                        self.user_line.create({
                            'first_name': user.name.split(' ', 1)[0],
                            'last_name': user.name.split(' ', 1)[
                                1] if ' ' in user.name else user.lastname or " ",
                            'email': user.email,
                            'app_user': user.id,
                            'employee_id': str(user.employee_id) or '',
                            'emp_discount_id': self.id
                        })
                        self.write({"user_ids": [(4, user.id)]})
            except Exception as e:
                _logger.error(str(e))
                raise UserError("Invalid File")


class EmployeeDiscountLine(models.Model):
    """Represents a line item for an employee discount setup."""
    _name = "employee.discount.line"
    _description = 'Employee Discount Line'

    first_name = fields.Char()
    last_name = fields.Char()
    email = fields.Char()
    employee_id = fields.Char()
    emp_discount_id = fields.Many2one(
        'employee.discount.setup', "Template", index=True)
    app_user = fields.Many2one(
        'res.app.users', string="User", ondelete="restrict")
    disable_user = fields.Boolean(
        string="Disable", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        """Creates a new record for an employee discount line and associates it with an app user."""
        records = []
        for vals in vals_list:
            email = vals.get('email')
            emp_discount_id = vals.get('emp_discount_id')
            user_id = self.env['res.app.users'].sudo().search(
                [('email', '=ilike', email)], limit=1)
            employee_discount = self.env[
                'employee.discount.setup'].sudo().search(
                [('id', '=', emp_discount_id)])
            if user_id:
                if user_id.id in employee_discount.user_line.app_user.ids:
                    continue  # skip creating the record
                else:
                    vals['app_user'] = user_id.id
                    rec = super().create([vals])
                    employee_discount.write({'user_ids': [(4, user_id.id)]})
                    records += rec
            else:
                user_exist = self.env['res.app.users'].sudo().create([{
                    'email': email,
                    'name': vals.get('first_name'),
                    'lastname': vals.get('last_name'),
                    'is_imported': True
                }])
                vals['app_user'] = user_exist.id
                rec = super().create([vals])
                employee_discount.write({'user_ids': [(4, user_exist.id)]})
                records += rec
        return records
    @api.onchange('email')
    def _onchange_email(self):
        """Validates the email address format when the email field changes."""
        if self.email:
            self.averigo_email_validation(self.email)
