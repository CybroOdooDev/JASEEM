# -*- coding: utf-8 -*-
from odoo.tools import is_html_empty
from odoo.tools.misc import get_lang
from odoo import models, fields, api, _


class MailActivityInherit(models.Model):
    _inherit = "mail.activity"

    def _domain_user_id(self):
        """ fun to set domain for users listing in activity wizard"""
        domain = [('user_type', '=', 'operator')]
        return domain

    @api.model
    def _default_activity_type_for_model(self, model):
        activity_type_model = self.env['mail.activity.type'].search(
            [('res_model', '=', model), ('company_id', '=', self.company_id.id)], limit=1)
        if activity_type_model:
            return activity_type_model
        activity_type_generic = self.env['mail.activity.type'].search(
            [('res_model', '=', False), ('company_id', '=', self.company_id.id)], limit=1)
        return activity_type_generic

    def _default_company_id(self):
        return self.env.company

    @api.model
    def _default_activity_type(self):
        default_vals = self.default_get(['res_model_id', 'res_model'])
        if not default_vals.get('res_model_id'):
            return False

        current_model = self.env["ir.model"].sudo().browse(
            default_vals['res_model_id']).model
        return self._default_activity_type_for_model(current_model)

    base_url = fields.Char('Survey Url')
    crm_id = fields.Many2one('crm.lead')
    activity_type_multi_id = fields.Many2one(
        'mail.activity.type', string='Activity Type',
        ondelete='restrict')
    user_id = fields.Many2one(
        'res.users', 'Assigned to',
        default=lambda self: self.env.user,
        domain=_domain_user_id,
        index=True, required=True)
    company_id = fields.Many2one('res.company', required=True,
                                 default=_default_company_id)
    activity_type_id = fields.Many2one(
        'mail.activity.type', string='Activity Type',
        domain="['|', ('res_model', '=', False), ('res_model', '=', res_model), ('company_id', '=', company_id)]",
        ondelete='restrict', default=_default_activity_type)

    @api.model_create_multi
    def create(self, vals_list):
        activities = super(MailActivityInherit, self).create(vals_list)

        # find partners related to responsible users, separate readable from unreadable
        if any(user != self.env.user for user in activities.user_id):
            user_partners = activities.user_id.partner_id
            readable_user_partners = user_partners._filter_access_rules_python(
                'read')
        else:
            readable_user_partners = self.env.user.partner_id

        # when creating activities for other: send a notification to assigned user;
        if self.env.context.get('mail_activity_quick_update'):
            activities_to_notify = self.env['mail.activity']
        else:
            activities_to_notify = activities.filtered(
                lambda act: act.user_id == self.env.user)
        if activities_to_notify:
            to_sudo = activities_to_notify.filtered(lambda
                                                        act: act.user_id.partner_id not in readable_user_partners)
            other = activities_to_notify - to_sudo
            to_sudo.sudo().action_notify()
            other.action_notify()

        # subscribe (batch by model and user to speedup)
        for model, activity_data in activities._classify_by_model().items():
            per_user = dict()
            for activity in activity_data['activities'].filtered(
                    lambda act: act.user_id):
                if activity.user_id not in per_user:
                    per_user[activity.user_id] = [activity.res_id]
                else:
                    per_user[activity.user_id].append(activity.res_id)
            for user, res_ids in per_user.items():
                pids = user.partner_id.ids if user.partner_id in readable_user_partners else user.sudo().partner_id.ids
                self.env[model].browse(res_ids).message_subscribe(
                    partner_ids=pids)

        # send notifications about activity creation
        todo_activities = activities.filtered(
            lambda act: act.date_deadline <= fields.Date.today())
        if todo_activities:
            self.env['bus.bus']._sendmany([
                (activity.user_id.partner_id, 'mail.activity/updated',
                 {'activity_created': True})
                for activity in todo_activities
            ])
        return activities

    def action_close_dialog(self):
        if self.res_model == 'crm.lead':
            self.crm_id = self.res_id
            if self.activity_type_id.name == 'Site Survey' and self.crm_id.stage_id.name == "New" and self.crm_id.type == 'opportunity':
                self.crm_id.stage_id = self.env.ref(
                    'averigo_crm.stage_lead02').id
                users = [self.user_id.id]
                self.crm_id.message_subscribe(users)
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    def action_notify(self):
        if self.activity_type_id.name == 'Site Survey':
            self.crm_id = self.res_id
            self.crm_id.activity_id = self.id
            survey_temp_id = self.activity_type_id.survey_template_id.id
            survey = self.env['survey.survey'].sudo().search(
                [('id', '=', survey_temp_id)])
            url = survey.get_start_url()
            self.base_url = url + '?res_id=%d' % self.res_id
            if not self:
                return
            for activity in self:
                if activity.user_id.lang:
                    # Send the notification in the assigned user's language
                    activity = activity.with_context(lang=activity.user_id.lang)

                model_description = activity.env['ir.model']._get(
                    activity.res_model).display_name
                body = activity.env['ir.qweb']._render(
                    'averigo_crm.message_survey_assigned',
                    {
                        'activity': activity,
                        'model_description': model_description,
                        'is_html_empty': is_html_empty,
                    },
                    minimal_qcontext=True
                )
                record = activity.env[activity.res_model].browse(
                    activity.res_id)
                if activity.user_id:
                    record.message_notify(
                        partner_ids=activity.user_id.partner_id.ids,
                        body=body,
                        record_name=activity.res_name,
                        model_description=model_description,
                        email_layout_xmlid=False,
                        subject=_('"%(activity_name)s: %(summary)s" assigned to you',
                                  activity_name=activity.res_name,
                                  summary=activity.summary or activity.activity_type_id.name),
                        subtitles=[_('Activity: %s', activity.activity_type_id.name),
                                   _('Deadline: %s', activity.date_deadline.strftime(get_lang(activity.env).date_format))]
                    )
        else:
            if not self:
                return
            for activity in self:
                if activity.user_id.lang:
                    # Send the notification in the assigned user's language
                    activity = activity.with_context(lang=activity.user_id.lang)

                model_description = activity.env['ir.model']._get(activity.res_model).display_name
                body = activity.env['ir.qweb']._render(
                    'mail.message_activity_assigned',
                    {
                        'activity': activity,
                        'model_description': model_description,
                        'is_html_empty': is_html_empty,
                    },
                    minimal_qcontext=True
                )
                record = activity.env[activity.res_model].browse(activity.res_id)
                if activity.user_id:
                    record.message_notify(
                        partner_ids=activity.user_id.partner_id.ids,
                        body=body,
                        record_name=activity.res_name,
                        model_description=model_description,
                        email_layout_xmlid='mail.mail_notification_layout',
                        subject=_('"%(activity_name)s: %(summary)s" assigned to you',
                                  activity_name=activity.res_name,
                                  summary=activity.summary or activity.activity_type_id.name),
                        subtitles=[_('Activity: %s', activity.activity_type_id.name),
                                   _('Deadline: %s', activity.date_deadline.strftime(get_lang(activity.env).date_format))]
                    )


class MailActivityType(models.Model):
    _inherit = "mail.activity.type"

    def _default_survey(self):
        """ to return default survey template"""
        survey = self.env['survey.survey'].sudo().search(
            [('title', '=', 'Grabscango Site Survey')])
        return survey

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    survey_template_id = fields.Many2one('survey.survey',
                                         string='Survey templates',
                                         default=_default_survey)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """ override the function to get mail for current user if the assignee is current user"""
        msg_sudo = message.sudo()
        # get values from msg_vals or from message if msg_vals doen't exists
        pids = msg_vals.get('partner_ids',
                            []) if msg_vals else msg_sudo.partner_ids.ids
        message_type = msg_vals.get(
            'message_type') if msg_vals else msg_sudo.message_type
        subtype_id = msg_vals.get(
            'subtype_id') if msg_vals else msg_sudo.subtype_id.id
        # is it possible to have record but no subtype_id ?
        recipients_data = []

        res = self.env['mail.followers']._get_recipient_data(self, message_type,
                                                             subtype_id, pids)[
            self.id if self else 0]
        if not res:
            return recipients_data

        # notify author of its own messages, False by default
        notify_author = kwargs.get('notify_author') or self.env.context.get(
            'mail_notify_author')
        real_author_id = False
        if not notify_author:
            if self.env.user.active:
                real_author_id = self.env.user.partner_id.id
            elif msg_vals.get('author_id'):
                real_author_id = msg_vals['author_id']
            else:
                real_author_id = message.author_id.id
        print(real_author_id, recipients_data, 2345555555466)
        for pid, pdata in res.items():
            print(pid, pdata, 343443)
            # if pid and pid == real_author_id:
            #     continue
            # if pdata['active'] is False:
            #     continue
            recipients_data.append(pdata)

        # avoid double notification (on demand due to additional queries)
        if kwargs.pop('skip_existing', False):
            pids = [r['id'] for r in recipients_data]
            if pids:
                existing_notifications = self.env[
                    'mail.notification'].sudo().search([
                    ('res_partner_id', 'in', pids),
                    ('mail_message_id', 'in', message.ids)
                ])
                recipients_data = [
                    r for r in recipients_data
                    if r['id'] not in existing_notifications.res_partner_id.ids
                ]
        print(recipients_data)

        return recipients_data

