# -*- coding: utf-8 -*-

from odoo.tools.safe_eval import safe_eval
from odoo import fields, models, api, _


class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'

    def _default_user_ids(self):
        """ fun to return admin users configured in sales teams"""
        users = self.env['crm.users.notify'].sudo().search([])
        return users.user_ids

    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.company,
                                 readonly=True)
    operator_id = fields.Many2one('res.company', string='Operator', index=True,
                                  default=lambda s: s.env.company.id)
    user_ids = fields.Many2many('res.users', string="Users",
                                default=_default_user_ids)

    @api.model
    def _action_update_to_pipeline(self, action):
        """ inherits addon function to change description"""
        user_team_id = self.env.user.sale_team_id.id
        if not user_team_id:
            user_team_id = self.search([], limit=1).id
            action['help'] = _("""<p class='o_view_nocontent_smiling_face'>Add new opportunities</p><p>
            Looks like you are not a member of a Sales Team. You should add yourself
            as a member of one of the Sales Team.
        </p>""")
            if user_team_id:
                action[
                    'help'] += "<p>As you don't belong to any Sales Team, AveriGo opens the first one by default.</p>"
        action_context = safe_eval(action['context'], {'uid': self.env.uid})
        if user_team_id:
            action_context['default_team_id'] = user_team_id

        action['context'] = action_context
        return action
