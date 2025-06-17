# -*- coding: utf-8 -*-
from logging import exception

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class IRImage(models.Model):
    """This model represents images that can be displayed on the App home screen."""
    _name = 'ir.image'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Home Screen Image'
    _order = 'create_date desc'
    _rec_name = 'image'

    name = fields.Char()
    image = fields.Binary(
        string='Image', required=True)
    active = fields.Boolean(
        string="Active", default=True)
    operator_id = fields.Many2many(
        comodel_name='res.company', relation='ir_image_res_company_rel', column1='image_id',
        column2='company_id',domain=[('is_main_company', '!=', True)],string="Operator")
    location = fields.Many2many(
        comodel_name='res.partner', relation='ir_image_res_partner_rel', column1='image_id',
        column2='partner_id', domain=[('is_customer', '=', True)])
    micro_market_id = fields.Many2many(
        comodel_name='stock.warehouse', relation='ir_image_stock_warehouse_rel', column1='image_id',
        column2='warehouse_id',domain=[('location_type', '=', 'micro_market')])
    start_date = fields.Date(
        string="Start Date")
    end_date = fields.Date(
        string="Stop Date")
    start_time = fields.Float(
        string="Start Time")
    end_time = fields.Float(
        string="Stop Time")
    banner_text = fields.Text(
        string="Banner Text")
    mm_ids = fields.Many2many(
        'stock.warehouse', 'ir_image_stock_warehouse_rel2',
        'image_id2', 'warehouse_id2')

    @api.onchange('operator_id')
    def operator_id_changed(self):
        """Updates the domain for the 'location' field based on the selected operators."""
        partner_ids = self.env['res.partner'].search([('company_id', 'in', self.operator_id.ids)]).ids
        return {
            'domain': {'location': [('is_customer', '=', True),
                                    ('operator_id', 'in', self.operator_id.ids)] if self.operator_id.ids else [
                ('is_customer', '=', True)]},
            'micro_market_id': [('location_type', '=', 'micro_market'), ('partner_id', 'in', partner_ids)]}

    @api.onchange('location')
    def location_changed(self):
        """Updates the domain for the 'micro_market_id' field based on the selected locations."""
        return {
            'domain': {
                'micro_market_id': [('partner_id', 'in', self.location.ids)] if self.location.ids else [
                    ('location_type', '=', 'micro_market')]
            }
        }

    @api.onchange('start_date', 'end_date', 'start_time', 'end_time')
    def onchange_check_dates(self):
        """Validates the start and end dates/times to ensure they are consistent."""
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise UserError(_("Inconsistent start and end dates! \n"
                                  "Stop date should be above the start date. "
                                  "Please check the date fields and try again."))
            if record.start_time and record.end_time and record.start_time >= record.end_time:
                raise UserError(_("Inconsistent start and end time! \n"
                                  "Stop time should be above the start time. "
                                  "Please check the time fields and try again."))
            if record.start_time < 0 or record.end_time < 0 or record.start_time > 24.0 or record.end_time > 24.0:
                raise UserError(_("Inconsistent start and end time! \n"
                                  "Time should be 0 to 24.0! "
                                  "Please check the time fields and try again."))
            if record.start_time and record.end_time and record.start_time == record.end_time:
                raise UserError(_("Start and End Time Can not be the same."))

    def get_featured_image(self, args):
        """Retrieves the featured image URL and banner text for a specified micro market and time."""
        try:
            micro_market = self.env['stock.warehouse'].browse(args['micro_market'])
            time = args['time'].split(' ')[1]
            date = args['time'].split(' ')[0]
            hours = float(time.split(':')[0])
            minutes = float(time.split(':')[1]) / 60 * 100
            timed_images = self.env['ir.image'].search(
                [('start_time', '<=', hours + (minutes / 100)), ('end_time', '>=', hours + (minutes / 100))])
            dated_images = self.env['ir.image'].search([('start_date', '<=', date), ('end_date', '>=', date)])
            ids = []
            if dated_images and timed_images:
                ids = list(set(timed_images.ids) & set(dated_images.ids))
            elif timed_images:
                ids = timed_images.ids
            elif dated_images:
                ids = dated_images.ids
            mm_images = self.env['ir.image'].search([('mm_ids', 'in', [micro_market.id])]).ids
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            ids = list(set(ids) & set(mm_images))
            if ids:
                rec = self.env['ir.image'].browse(ids[0])
                return {'image_url': base_url + '/web/image_get?model=ir.image&id=' + str(rec.id) + '&field=image',
                        'banner_text': rec.banner_text}
            else:
                return {'image_url': False,
                        'banner_text': False}
        except Exception as e:
            return {'image_url': False,
                    'banner_text': False}

    @api.model
    def create(self, vals_list):
        """Overrides the default create method to handle additional logic for setting 'mm_ids'."""
        if 'micro_market_id' in vals_list and vals_list['micro_market_id'] and vals_list['micro_market_id'][0][1]:
            vals_list['mm_ids'] = vals_list['micro_market_id']
        else:
            field = 'location' if 'location' in vals_list else 'operator_id'
            if field in vals_list and vals_list[field] and vals_list[field][0] and vals_list[field][0][1]:
                ids = [sublist[1] for sublist in vals_list[field]]
                model_field = 'partner_id' if field == 'location' else 'company_id'
                vals_list['mm_ids'] = [[6, False, self.env['stock.warehouse'].search([(model_field, 'in', ids)]).ids]]
            else:
                vals_list['mm_ids'] = [[6, False, self.env['stock.warehouse'].search([]).ids]]
        res = super().create(vals_list)
        cr = self._cr
        query = f"SELECT id, start_time, end_time FROM ir_image WHERE id != {res.id}"
        if res.start_date and res.end_date:
            query += f" AND ('{res.start_date}'::DATE, '{res.end_date}'::DATE) OVERLAPS (start_date, end_date)"
        query += f" AND ((start_time <= '{res.start_time}' AND end_time >= '{res.start_time}') OR (start_time >= '{res.end_time}' AND end_time <= '{res.end_time}'))"
        cr.execute(query)
        data = cr.dictfetchall()
        if data:
            overlapping_mm_ids = set(self.env['ir.image'].browse([d['id'] for d in data]).mapped('mm_ids').ids) & set(
                res.mm_ids.ids)
            if overlapping_mm_ids:
                mm = res.env['stock.warehouse'].browse(overlapping_mm_ids.pop())
                raise UserError(
                    _(f"This image time and date overlaps an existing image for Micro Market {mm.name}"))
        return res

    def write(self, vals_list):
        """Overrides the default write method to handle additional logic for setting 'mm_ids'."""
        if 'micro_market_id' in vals_list:
            vals_list['mm_ids'] = vals_list['micro_market_id']
        else:
            field = 'location' if 'location' in vals_list else 'operator_id'
            if field in vals_list:
                partners = [sublist[1] for sublist in vals_list[field]]
                warehouse_ids = self.env['stock.warehouse'].search([('partner_id', 'in', partners)]).ids
                vals_list['mm_ids'] = [[6, False, warehouse_ids]]
            else:
                vals_list['mm_ids'] = [[6, False, self.env['stock.warehouse'].search([]).ids]]
        res = super().write(vals_list)
        cr = self._cr
        date_condition = f"('{self.start_date}'::DATE, '{self.end_date}'::DATE) OVERLAPS (start_date, end_date) and " if self.start_date and self.end_date else ""
        query = f"""
            SELECT id, start_time, end_time FROM ir_image 
            WHERE {date_condition} id != {self.id} 
            AND ((start_time <= '{self.start_time}' AND end_time >= '{self.start_time}') 
            OR (start_time >= '{self.end_time}' AND end_time <= '{self.end_time}'))
        """
        cr.execute(query)
        data = cr.dictfetchall()
        if data:
            overlapping_image = self.browse(data[0]['id'])
            common_mm_ids = set(overlapping_image.mm_ids.ids) & set(self.mm_ids.ids)
            if common_mm_ids:
                mm = self.env['stock.warehouse'].browse(common_mm_ids.pop())
                raise UserError(_(f"This image time and date overlaps an existing image for Micro Market {mm.name}"))
        return res

