# -*- coding: utf-8 -*-

from odoo import fields, models


class CrmStageInherit(models.Model):
    _inherit = 'crm.stage'

    company_id = fields.Many2one('res.company', string="Operator",
                                 default=lambda self: self.env.company)
    stage_percentage = fields.Float(string="% Probability By Stage")
    is_closed_stage = fields.Boolean(string="Is Closed Stage")
