# -*- coding: utf-8 -*-
import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class CRMLead2OpportunityPartnerInherit(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    def action_apply(self):
        """Convert lead to opportunity or merge lead and opportunity and open
        the freshly created opportunity view."""
        result_opportunity = self._action_convert()
        return result_opportunity.redirect_lead_opportunity_view()

    def convert_lead(self):
        """Action for converting lead to opportunity."""
        self.action = 'nothing'
        return self.action_apply()

    def create_customer(self):
        """Create customer while converting lead to opportunity."""
        self.ensure_one()
        self.action = 'create'
        values = {
            'team_id': self.team_id.id,
        }
        
        if self.partner_id:
            values['partner_id'] = self.partner_id.id
            
        leads = self.env['crm.lead'].browse(self._context.get('active_ids', []))
        values.update({
            'lead_ids': leads.ids,
            'user_ids': [self.user_id.id]
        })

        for lead in leads:
            if lead.active and self.action != 'nothing':
                partner_id = self._convert_handle_partner(
                    lead,
                    self.action,
                    self.partner_id.id or lead.partner_id.id
                )
            lead.convert_opportunity(
                lead.partner_id.id,
                user_ids=False,
                team_id=False
            )

        user_ids = values.get('user_ids')
        leads_to_allocate = leads
        
        if not self.force_assignment:
            leads_to_allocate = leads_to_allocate.filtered(
                lambda lead: not lead.user_id
            )
            
        if user_ids:
            leads_to_allocate._handle_salesmen_assignment(
                user_ids,
                team_id=values.get('team_id')
            )

        res = leads[0].redirect_lead_opportunity_view()
        res['name'] = self.partner_id.name
        res['res_id'] = leads[0].partner_id.id
        res['res_model'] = 'res.partner'
        res['context'].update({'default_type': 'contact'})
        
        return res

    def action_set_won_rainbowman(self):
        """Set customer context in partner while opportunity won."""
        if self.partner_id:
            self.partner_id.is_customer = True
        return super(CRMLead2OpportunityPartnerInherit,
                    self).action_set_won_rainbowman()