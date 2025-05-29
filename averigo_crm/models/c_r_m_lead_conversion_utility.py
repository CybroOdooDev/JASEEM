# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class CRMLead2OpportunityPartnerInherit(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def action_apply(self):
        """Convert lead to opportunity and redirect to the opportunity view."""
        result = self._action_convert()
        return result.redirect_lead_opportunity_view()

    def convert_lead(self):
        """Convert lead to opportunity without partner creation."""
        self.action = 'nothing'
        return self.action_apply()

    def create_customer(self):
        """Convert lead and create customer if required."""
        self.ensure_one()
        self.action = 'create'
        leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))

        values = {
            'team_id': self.team_id.id,
            'lead_ids': leads.ids,
            'user_ids': [self.user_id.id],
        }
        if self.partner_id:
            values['partner_id'] = self.partner_id.id

        for lead in leads:
            if lead.active and self.action != 'nothing':
                self._convert_handle_partner(
                    lead,
                    self.action,
                    self.partner_id.id or lead.partner_id.id
                )
            lead.convert_opportunity(
                lead.partner_id.id,
                user_ids=False,
                team_id=False
            )

        if not self.force_assignment:
            leads = leads.filtered(lambda l: not l.user_id)

        if values['user_ids']:
            leads._handle_salesmen_assignment(
                values['user_ids'],
                team_id=values['team_id']
            )

        res = leads[0].redirect_lead_opportunity_view()
        res.update({
            'name': self.partner_id.name,
            'res_id': leads[0].partner_id.id,
            'res_model': 'res.partner',
        })
        res['context'].update({'default_type': 'contact'})
        return res

    def action_set_won_rainbowman(self):
        """Mark partner as customer when opportunity is won."""
        if self.partner_id:
            self.partner_id.is_customer = True
        return super().action_set_won_rainbowman()

