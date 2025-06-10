# -*- coding: utf-8 -*-

from odoo import models, fields, _


class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'

    reports_to = fields.Char(string="Email Reports To")
    from_lead = fields.Boolean(string="Is Created From Lead", default=False)
    mail_activities_count = fields.Integer(
        compute="_compute_planned_mail_activities")
    close_activities_count = fields.Integer()

    opportunity_count = fields.Integer(
        string="Opportunity Count",
        groups='sales_team.group_sale_salesman,base_averigo.averigo_operator_user_group',
        compute='_compute_opportunity_count',
    )

    def _compute_planned_mail_activities(self):
        """ To get the count of planned activities in customer"""
        for rec in self:
            recs = rec.env['mail.activity'].sudo().search(
                [('res_id', '=', rec.id),
                 ('res_model', '=', 'res.partner')]).ids
            rec.mail_activities_count = len(recs) if recs else 0

    def open_my_activities(self):
        """ Smart button to view planned activities"""
        return {
            'name': _('Planned Activities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'views': [(self.env.ref(
                'averigo_crm.planned_activity_view_tree').id,
                       'tree'), (self.env.ref(
                'averigo_crm.planned_activity_view_form').id,
                                 'form')],
            'res_model': 'mail.activity',
            'target': 'current',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', 'res.partner')],
            'context': {'default_res_model': 'res.partner',
                        'default_res_id': self.id}
        }

    def open_my_opportunities(self):
        """ smart button to open opportunities in a partner"""
        return {
            'name': _('Opportunities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'crm.lead',
            'target': 'current',
            'domain': [('partner_id', '=', self.id),
                       ('type', '=', 'opportunity')],
            'context': {'default_type': 'opportunity',
                        'default_partner_id': self.id}
        }

    def close_my_activities(self):
        """Function for smart button closed activities in customer care"""
        print('t5')
