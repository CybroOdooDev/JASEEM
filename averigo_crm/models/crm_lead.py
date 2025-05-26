# -*- coding: utf-8 -*-
from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from odoo.tools.translate import _


class CRMLead(models.Model):
    """inherit crm.lead model to add averigo specific fields"""
    _inherit = 'crm.lead'
    order = 'create_date desc'

    def _default_stage_id(self):
        """ to return New stage Declared in this module"""
        return self.env.ref('averigo_crm.stage_lead01').id

    status = fields.Many2one('crm.lead.status', string="Status")
    first_name = fields.Char(string="First Name", size=78)
    middle_name = fields.Char(string="Contact Name", size=78)
    last_name = fields.Char(string="Last Name", size=78)
    partner_name = fields.Char(string="Company Name", size=78, required=False)
    user_id = fields.Many2one('res.users', string="Lead Owner", required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer', tracking=10, index=True,
        domain=[
            ('is_customer', '=', True),
            ('parent_id', '=', False),
            ('type', '=', 'contact')
        ],
        help="Linked partner (optional). Usually created when converting the lead. "
             "You can find a partner by its Name, TIN, Email or Internal Reference."
    )
    no_of_rooms = fields.Integer(string="Room")
    checkin_frequency = fields.Char(string="Occupancy Rate")
    visitors_types_ids = fields.Many2many(
        'crm.visitor.types', string="Types Of visitors"
    )
    stage_id = fields.Many2one(
        'crm.stage', default=_default_stage_id,
        group_expand='_read_group_stage_ids'
    )
    activity_id = fields.Many2one('mail.activity')
    survey_answer_id = fields.Many2one('survey.user_input')
    parent_lead_id = fields.Integer('Parent Lead Id')
    answer_count = fields.Integer(compute="_compute_answers_count")
    is_activity_scheduled = fields.Boolean('Site Survey Scheduled')
    is_site_survey_stage = fields.Boolean(
        'Site survey stage', compute='_compute_stages'
    )
    is_proposal_stage = fields.Boolean(
        'Proposal stage', compute='_compute_stages'
    )
    is_agreement_stage = fields.Boolean(
        'Agreement stage', compute='_compute_stages'
    )
    is_sow_stage = fields.Boolean('Sow stage', compute='_compute_stages')
    is_won_stage = fields.Boolean('Won stage', compute='_compute_stages')
    opportunity_url = fields.Char('Lead url')
    account_id = fields.Many2one('docusign.credentials', 'DocuSign Account')
    document = fields.Char(string='Agreements')
    complete_document = fields.Char('Agreement Status')
    attach_id = fields.Many2one('ir.attachment', string='Signed Attachments')
    indication_note = fields.Text(tracking=True)
    sow_document = fields.Char(string='Sow')
    sow_complete_document = fields.Char('Status')
    sow_attach_id = fields.Many2one('ir.attachment', string='Sow Documents')
    sow_indication_note = fields.Text(tracking=True)
    lead_transfer_url = fields.Char('Lead Transfer url')
    _sql_constraints = [
        (
            'check_probability',
            'check(probability >= 0 and probability <= 100)',
            'The probability of closing the deal should be between 0% and 100%'
        )
    ]

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        """Override to set proper domain for stage selection"""
        # retrieve team_id from the context and write the domain
        # - ('id', 'in', stages.ids): add columns that should be present
        # - OR ('fold', '=', False): add default columns that are not folded
        # - OR ('team_ids', '=', team_id), ('fold', '=', False) if team_id:
        #   add team columns that are not folded
        team_id = self._context.get('default_team_id')
        if team_id:
            search_domain = [
                '|', ('id', 'in', stages.ids), '|',
                ('team_id', '=', False), ('team_id', '=', team_id),
                ('is_averigo_stage', '=', True)
            ]
        else:
            search_domain = [
                '|', ('id', 'in', stages.ids),
                ('team_id', '=', False),
                ('is_averigo_stage', '=', True)
            ]
        # perform search
        stage_ids = stages._search(
            search_domain
        )
        return stages.browse(stage_ids)

    @api.depends('stage_id')
    def _compute_stages(self):
        """ To compute stages and assign values to boolean fields"""
        for record in self:
            # Reset all stage flags
            record.is_site_survey_stage = False
            record.is_proposal_stage = False
            record.is_agreement_stage = False
            record.is_sow_stage = False
            record.is_won_stage = False

            # Set appropriate flag based on current stage
            if record.stage_id.id == self.env.ref(
                    'averigo_crm.stage_lead02').id:
                record.is_site_survey_stage = True
            elif record.stage_id.id == self.env.ref(
                    'averigo_crm.stage_lead03').id:
                record.is_proposal_stage = True
            elif record.stage_id.id == self.env.ref(
                    'averigo_crm.stage_lead04').id:
                record.is_agreement_stage = True
            elif record.stage_id.id == self.env.ref(
                    'averigo_crm.stage_lead05').id:
                record.is_sow_stage = True
            elif record.stage_id.id == self.env.ref('crm.stage_lead4').id:
                record.is_won_stage = True

    @api.onchange('zip')
    def get_address(self):
        """ to fill address when zip value is filled"""
        if self.zip:
            self.zip = '{:0>5}'.format(self.zip)

        address_details = self.env['zip.county'].search(
            [('zip', '=', self.zip)], limit=1
        )
        if address_details:
            state_id = self.env['res.country.state'].search(
                [
                    ('code', '=', address_details.state),
                    ('country_id', '=', self.env.ref('base.us').id)
                ],
                limit=1
            )
            self.state_id = state_id.id if state_id else False
            self.city = address_details.city

    @api.model
    def create(self, vals_list):
        """overrides create function"""
        if 'first_name' in vals_list and 'last_name' in vals_list:
            first = vals_list.get('first_name', '')
            middle = vals_list.get('middle_name', '')
            last = vals_list.get('last_name', '')

            if first or middle or last:
                contact_name_parts = []
                if first:
                    contact_name_parts.append(first)
                if middle:
                    contact_name_parts.append(middle)
                if last:
                    contact_name_parts.append(last)

                vals_list['contact_name'] = " ".join(contact_name_parts)

        return super(CRMLead, self).create(vals_list)

    def _prepare_customer_values(self, partner_name, is_company=False,
                                 parent_id=False):
        """ overrides addon function to include is_customer context"""
        res = super(CRMLead, self)._prepare_customer_values(
            partner_name, is_company, parent_id
        )
        res['is_customer'] = True
        return res

    def convert_opportunity(self, partner, user_ids=False, team_id=False):
        """ override convert opportunity function to add customer"""
        customer = False
        if partner:
            customer = (
                    self.env['res.partner'].browse(partner).parent_id or
                    self.env['res.partner'].browse(partner)
            )
            customer.is_customer = True
            customer.customer_rank = 1

        for lead in self:
            if not lead.active or lead.probability == 100:
                continue
            vals = lead._convert_opportunity_data(customer, team_id)
            lead.write(vals)

        if user_ids or team_id:
            self._handle_salesmen_assignment(user_ids=user_ids, team_id=team_id)
        return True

    def create_account(self):
        """ To Create Customer From Opportunity"""
        print("Ahmmmmmm", self.partner_name)
        customer = self.env['res.partner'].with_context(
            default_is_customer=True
        ).create({
            'name': self.partner_name,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state_id': self.state_id.id,
            'email': self.email_from,
            'zip': self.zip,
            'is_customer': True,
            'type': 'contact'
        })
        self.partner_id = customer.id
        print("customer", customer)

        return {
            'name': _("Proposal"),
            'view_mode': 'form',
            'view_id': self.env.ref(
                'averigo_base_customer.res_partner_operator_action').id,
            'view_type': 'form',
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'res_id': customer.id,
            'context': {'is_customer': True, 'active_id': customer.id},
            'target': 'current',

        }

    def action_view_sale_quotation(self):
        """ To view Quotations(Smart Button action)"""
        action = self.env.ref(
            'averigo_sales_order.action_customer_quotations'
        ).read()[0]

        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [
            ('opportunity_id', '=', self.id),
            ('state', 'in', ['draft', 'sent'])
        ]

        quotations = self.mapped('order_ids').filtered(
            lambda l: l.state in ('draft', 'sent')
        )

        if len(quotations) == 1:
            action['views'] = [(
                self.env.ref(
                    'averigo_sales_order.view_sale_order_customer_form'
                ).id,
                'form'
            )]
            action['res_id'] = quotations.id

        return action

    def action_site_survey(self):
        """ Fun to schedule survey"""
        ctx = dict(
            default_res_id=self.id,
            default_res_model='crm.lead',
        )
        return {
            'name': _('Schedule an Activity'),
            'context': ctx,
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_survey_user_input_completed(self):
        """ action to view survey answers"""
        surveys = self.env['mail.activity.type'].search([
            ('name', '=', "Site Survey"),
            ('company_id', '=', self.company_id.id)
        ])

        if self.parent_lead_id:
            survey_answer_id = self.env['survey.user_input'].search([
                ('lead_id', '=', self.parent_lead_id),
                ('state', '=', 'done')
            ], order='create_date desc')
        else:
            survey_answer_id = self.env['survey.user_input'].search([
                ('lead_id', '=', self.id),
                ('state', '=', 'done')
            ], order='create_date desc')

        return {
            "name": self.name,
            "type": "ir.actions.act_window",
            "res_model": "survey.user_input",
            'domain': [('id', 'in', survey_answer_id.ids)],
            "view_mode": "tree,form"
        }

    def _compute_answers_count(self):
        """ To get the count of survey answers in opportunity form"""
        for record in self:
            record.answer_count = False
            # surveys = self.env['mail.activity.type'].search([
            #     ('name', '=', "Site Survey"),
            #     ('company_id', '=', self.company_id.id)
            # ])
            #
            # for recd in record.activity_ids:
            #     if surveys.name == recd.activity_type_id.name:
            #         self.is_activity_scheduled = True
            #
            # rec_id = self.env['survey.user_input'].search([
            #     ('lead_id', '=', self.id),
            #     ('state', '=', 'done')
            # ], order='create_date desc', limit=1)
            #
            # record_id = self.env['survey.user_input'].search([
            #     ('lead_id', '=', self.parent_lead_id),
            #     ('state', '=', 'done')
            # ], order='create_date desc', limit=1)
            #
            # record.answer_count = 1 if (rec_id or record_id) else 0

    def write(self, vals):
        """overrides write function to send mail for state change"""
        if 'probability' in vals and self.active is False:
            vals.update({'active': True})

        res = super(CRMLead, self).write(vals)

        if 'stage_id' in vals:
            base_url = self.env.user.company_id.exact_domain
            print("base_urlllllllllll", base_url)
            base_url = f"{base_url}/web#id={self.id}&view_type=form&model={self._name}"

            self.opportunity_url = base_url

            if self.team_id.user_ids:
                for users in self.team_id.user_ids:
                    template = self.env.ref(
                        'averigo_crm.message_state_assigned'
                    )
                    template.write({'email_to': users.partner_id.email})
                    template.sudo().send_mail(res_id=self.id, force_send=True)

        return res

    def action_share_survey(self):
        """Function to share survey with contacts"""
        activity = self.env['mail.activity.type'].search([
            ('name', '=', "Site Survey"),
            ('company_id', '=', self.company_id.id)
        ])

        template = self.env.ref(
            'averigo_crm.mail_template_user_input_invite_custom',
            raise_if_not_found=False
        )

        survey = self.env['survey.survey'].sudo().search([
            ('id', '=', activity.survey_template_id.id)
        ])

        default_survey_url = survey.get_start_url() + '?res_id=%d' % self.id

        local_context = dict(
            self.env.context,
            default_crm_id=self.id,
            default_survey_id=activity.survey_template_id.id,
            default_survey_start_url=default_survey_url,
            default_send_email=True,
            default_template_id=template and template.id or False,
            default_email_layout_xmlid='mail.mail_notification_light',
        )

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'survey.invite',
            'target': 'new',
            'context': local_context,
        }

    def action_proposal(self):
        """ proposal state function"""
        record_id = self.env['survey.user_input'].search([
            ('lead_id', '=', self.id),
            ('state', '=', 'done')
        ], order='create_date desc', limit=1)

        if not record_id:
            raise UserError(
                _('Survey form should be filled to move to proposal state.')
            )
        else:
            view_id = self.env.ref(
                'averigo_crm.proposal_action_wizard_view'
            ).id

            return {
                'name': _("Proposal"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'proposal.action.wizard',
                'type': 'ir.actions.act_window',
                'target': 'new'
            }

    def proposal_attachments(self):
        """ to view proposal attachments"""
        record = self.env['proposal.action.wizard'].search([
            ('crm', '=', self.id)
        ], order='create_date desc')

        return {
            "name": 'Proposal',
            "type": "ir.actions.act_window",
            "res_model": "proposal.action.wizard",
            "domain": [('attachment_ids', 'in', record.attachment_ids.ids)],
            "view_mode": "list"
        }

    def action_agreement(self):
        """ Fun to move to agreement stage"""
        view_id = self.env.ref(
            'averigo_crm.agreement_action_wizard_view'
        ).id

        res_id = self.env['agreement.action.wizard'].create({
            'crm': self.id,
            'email_id': self.partner_id.id,
        })

        return {
            'name': _("Agreement"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'agreement.action.wizard',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def agreement_document_status(self):
        """ To View the Completed Agreement"""
        self.account_id = self.env['docusign.credentials'].search([], limit=1)
        documents = self

        if len(documents) == 0:
            documents = self.search([])

        model_info = {'model_name': str(self._inherit)}

        if self.complete_document == 'completed' and self.attach_id:
            return {
                "name": 'Documents',
                "type": "ir.actions.act_window",
                "res_model": "ir.attachment",
                "res_id": self.attach_id.id,
                "view_mode": "form"
            }
        else:
            print("jjjjjjjjjj", documents, model_info)
            self.env['docusign.send'].document_status(documents, model_info)

            if self.complete_document == 'completed':
                return {
                    "name": 'Documents',
                    "type": "ir.actions.act_window",
                    "res_model": "ir.attachment",
                    "res_id": self.attach_id.id,
                    "view_mode": "form"
                }
            else:
                raise UserError(
                    'No documents are fully completed by all recipients'
                )

    def action_sow(self):
        """ Function To move to SOW Stage"""
        view_id = self.env.ref('averigo_crm.sow_action_wizard_view').id
        res_id = self.env['sow.action.wizard'].create({'crm': self.id})
        print("res_id", res_id)

        return {
            'name': _("SOW"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'sow.action.wizard',
            'res_id': res_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def sow_document_status(self):
        """ To View the Completed SOW document"""
        self.account_id = self.env['docusign.credentials'].search([], limit=1)
        documents = self
        print("lklklklklkkl", self._inherit)

        if len(documents) == 0:
            documents = self.search([])

        model_info = {'model_name': str(self._inherit)}

        if self.sow_complete_document == 'completed' and self.sow_attach_id:
            return {
                "name": 'Sow Documents',
                "type": "ir.actions.act_window",
                "res_model": "ir.attachment",
                "res_id": self.sow_attach_id.id,
                "view_mode": "form"
            }
        else:
            print("jjjjjjjjjjjj", documents, model_info)

            if self.sow_complete_document == 'completed':
                return {
                    "name": 'Sow Documents',
                    "type": "ir.actions.act_window",
                    "res_model": "ir.attachment",
                    "res_id": self.sow_attach_id.id,
                    "view_mode": "form"
                }
            else:
                raise UserError('SOW document is not filled.')

    def action_transfer(self):
        """ To Transfer Lead Between Operators"""
        view_id = self.env.ref('averigo_crm.transfer_lead_wizard_view').id

        return {
            'name': _("Operator"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'transfer.lead.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
