from odoo import fields, models, api


class UpcScanFailure(models.Model):
    _name = 'upc.scan.failure'
    _description = 'UPC Scan Failure'

    date = fields.Char('Date', readonly=True)
    location_id = fields.Many2one('stock.warehouse', readonly=True)
    app_version = fields.Char('App Version', readonly=True)
    user_id = fields.Many2one('res.app.users', readonly=True)
    upc_code = fields.Char('UPC Code', readonly=True)
    company_id = fields.Many2one('res.company', related='location_id.company_id', store=True, string='Operator')
