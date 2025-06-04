# Filename: controllers/crm_ebitda_api.py

from odoo import http
from odoo.http import request

class CRMEbitdaController(http.Controller):

    @http.route('/crm/ebitda/stages', type='json', auth='user')
    def get_crm_stages_with_ebitda(self):
        """Return all CRM stages with related EBITDA total from leads"""
        # Fetch all CRM stages
        stages = request.env['crm.stage'].sudo().search([])

        result = []
        for stage in stages:
            # Search leads in this stage
            leads = request.env['crm.lead'].sudo().search([('stage_id', '=', stage.id)])
            # Calculate total EBITDA for the leads in this stage
            total_ebitda = sum(lead.ebitda for lead in leads if lead.ebitda)

            result.append({
                'stage_name': stage.name,
                'stage_id': stage.id,
                'total_ebitda': total_ebitda,
                'lead_count': len(leads),
            })

        return {'status': 'success', 'data': result}
