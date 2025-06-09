# -*- coding: utf-8 -*-
import json
from datetime import datetime
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class NotificationSetup(models.Model):
    """Represents the settings for different types of notifications."""
    _name = "notification.setup"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Notification Settings'
    _rec_name = 'notification_type'

    notification_type = fields.Selection(
        selection=[('special', 'Special  Notification'), ('featured', 'Featured Notification')],
        string="Notification Type", default='special')
    notification_time = fields.Float(
        string='Notification Time')

    @api.model_create_multi
    def create(self, vals_list):
        """ create function"""
        res = super().create(vals_list)
        for vals in vals_list:
            time = vals.get('notification_time')
            if time is not None and not (0.0 <= time <= 24.0):
                raise UserError(
                    _("Please enter a valid time between 0.0 and 24.0 hours."))
        return res

    def write(self, vals):
        """Override the write method to add the validation."""
        res = super().write(vals)
        time = vals.get('notification_time')
        if time is not None and not (0.0 <= time <= 24.0):
            raise UserError(
                _("Please enter a valid time between 0.0 and 24.0 hours."))
        return res

class FireBaseNotification(models.Model):
    _name = 'fire.base.notification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Fire Base Notification'
    _rec_name = 'title'

    title = fields.Char(
        string='Notification Title', tracking=True)
    user_type = fields.Selection(
        selection=[('normal', 'All Users')], string="Send To", default='normal')
    content = fields.Char(
        string='Content')
    web_url = fields.Char(
        string='We URL')
    image = fields.Image(
        string='Image')
    sent = fields.Boolean(
        string='sent', copy=False)
    sent_date = fields.Datetime(
        string='sent', copy=False)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('done', 'Sent')], string="Status",
        default='draft', copy=False)

    def send_notification(self):
        print(11111122)
        self.state = 'done'
