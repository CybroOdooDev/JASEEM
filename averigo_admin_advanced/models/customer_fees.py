# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timezone
from odoo.exceptions import UserError, ValidationError


class CustomerFees(models.Model):
    _name = "customer.fees"
    _description = 'Customer Fees'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    def _get_country(self):
        """ Get default country as United States"""
        country = self.env.ref('base.us').id
        return country

    name = fields.Char('Company Name', tracking=True)
    active = fields.Boolean(string="Active", default=True)
    type_id = fields.Many2one('customer.fees.type', tracking=True, ondelete='restrict')
    id_number = fields.Char('EIN/SSN', tracking=True, copy=False)
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=5, tracking=True)
    city = fields.Char('City')
    county = fields.Char('County')
    state_id = fields.Many2one('res.country.state', string="State",
                               domain="[('country_id', '=', country_id)]")
    country_id = fields.Many2one('res.country', string="Country",
                                 default=_get_country)
    address = fields.Char(compute='_compute_address', store=True)
    primary_contact = fields.Char('Primary Contact', tracking=True)
    primary_email = fields.Char('Primary Email', tracking=True)
    primary_phone = fields.Char('Primary Phone', tracking=True)
    primary_mobile = fields.Char('Primary Mobile', tracking=True)
    accounts_payable_contact = fields.Char('Accounts Payable Contact',
                                           tracking=True)
    accounts_payable_email = fields.Char('Accounts Payable Email',
                                         tracking=True)
    accounts_payable_phone = fields.Char('Accounts PayablePhone', tracking=True)
    accounts_payable_mobile = fields.Char('Accounts PayableMobile',
                                          tracking=True)
    attachment_ids_1099 = fields.Many2many('ir.attachment',
                                           'form_1099_attachment',
                                           string='1099 Form')
    date_1099_attached = fields.Date()
    attachment_ids_banking_info = fields.Many2many('ir.attachment',
                                                   'banking_info_attachment',
                                                   string='Banking Information')
    attachment_ids_contract = fields.Many2many('ir.attachment',
                                               'contract_attachment',
                                               string='Contract')
    attachment_ids_others = fields.Many2many('ir.attachment',
                                             'others_attachment',
                                             string='Others')
    comment = fields.Text(string="Internal notes")
    special_notes = fields.Text(string="Special Notes")

    @api.onchange('zip')
    def get_zip_address(self):
        """ Get zip address """
        country = self.env.ref('base.us')
        if self.zip:
            zip_address = self.env['zip.county'].sudo().search(
                [('zip', '=', self.zip)], limit=1)
            if zip_address.id:
                state_id = self.env['res.country.state'].sudo().search(
                    [('code', '=', zip_address.state),
                     ('country_id', '=', country.id)], limit=1)
                self.state_id = state_id.id if state_id else False
                self.city = zip_address.city
                self.county = zip_address.county
            else:
                raise UserError(
                    _("Invalid zip code.Please try again."))

    @api.onchange('attachment_ids_1099')
    def onchange_attachment_ids_1099(self):
        """Update the attachment date based on whether files are attached"""
        self.date_1099_attached = fields.Datetime.now() if self.attachment_ids_1099 else False

    @api.depends('street', 'street2', 'city', 'state_id', 'zip', 'country_id')
    def _compute_address(self):
        """Make the address in a single field """
        for rec in self:
            address = [
                rec.zip,
                rec.street,
                rec.street2,
                rec.city,
                rec.state_id.code,
            ]
            rec.address = ','.join([p for p in address if p])


class CustomerFeesType(models.Model):
    _name = "customer.fees.type"
    _description = 'Customer Fees Type'

    name = fields.Char(required=1, string='Name')
    readonly = fields.Boolean()
    restrict_delete = fields.Boolean()

    @api.constrains('name')
    def _check_name_constraint(self):
        """ Name must be unique """
        for rec in self:
            if self.env['customer.fees.type'].search(
                [('id', '!=', rec.id), ('name', '=', rec.name)]):
                raise ValidationError(_('The Name is already exists!'))

    def unlink(self):
        for rec in self:
            if rec.restrict_delete:
                raise UserError(_("This Fees Type cannot be deleted."))
        return super(CustomerFeesType, self).unlink()


