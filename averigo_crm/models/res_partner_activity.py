from odoo import models, fields, _


class ResPartnerActivityInherit(models.Model):
    _inherit = 'res.partner'

    close_activities_count = fields.Integer(compute="closed_mail_activities")

    def closed_mail_activities(self):
        for rec in self:
            # print(rec.env['mail.activity'].search([('res_id', '=', rec.id), ('res_model', '=', 'res.partner')]))
            recs = rec.env['done.activity.datas'].sudo().search([('res_id', '=', rec.id), ('res_model', '=', 'res.partner')]).ids
            rec.close_activities_count = len(recs) if recs else 0

    def close_my_activities(self):
        return {
            'name': _('Closed Activities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'done.activity.datas',
            'target': 'current',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', 'res.partner')],
            'context': {'default_res_model': 'res.partner',
                        'default_res_id': self.id}
        }

    def open_my_activities(self):
        return {
            'name': _('Planned Activities'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'views': [(self.env.ref('averigo_crm_update.planned_activity_view_tree').id,
                       'tree'), (self.env.ref('averigo_crm_update.planned_activity_view_form').id,
                       'form')],
            'res_model': 'mail.activity',
            'target': 'current',
            'domain': [('res_id', '=', self.id), ('res_model', '=', 'res.partner')],
            'context': {'default_res_model': 'res.partner', 'default_res_id': self.id}
        }