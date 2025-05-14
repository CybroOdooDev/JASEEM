# -*- coding: utf-8 -*-

from odoo import fields, models, api


class CRMLeadStatus(models.Model):
    """CRM lead status model, records of this model will be selected as status"""
    _name = 'crm.lead.status'
    _description = "CRM Lead Status"

    name = fields.Char("Status")
    company_id = fields.Many2one('res.company', string="Operator", default=lambda self: self.env.company)
    active = fields.Boolean(string="Active", default=True)


class Visitors(models.Model):
    """ CRM visitor Types"""
    _name = 'crm.visitor.types'
    _rec_name = 'visitors'
    _description = "CRM Visitor Types"

    visitors = fields.Char(string="Visitors Types")


class CrmStages(models.Model):
    _inherit = 'crm.stage'

    is_averigo_stage = fields.Boolean(string="Is Averigo Stage", default=False)
