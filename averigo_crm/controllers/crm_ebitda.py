from odoo import http
from odoo.http import request

class KanbanEbitdaController(http.Controller):

    @http.route('/ebitda/kanban/data', type='json', auth='user')
    def get_ebitda_data(self):
        stages = request.env['crm.stage'].sudo().search([])
        result = []
        for stage in stages:
            leads = request.env['crm.lead'].sudo().search([('stage_id', '=', stage.id)])
            total_ebitda = sum(lead.ebitda or 0 for lead in leads)
            result.append({
                'stage_id': stage.id,
                'stage_name': stage.name,
                'total_ebitda': total_ebitda,
            })
        return result
