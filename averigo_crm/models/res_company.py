from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    dynamic_stages_in_crm = fields.Boolean(string="Dynamic Stages in CRM")
    site_survey_activity_id = fields.Many2one(
        "mail.activity.type",
        string="Site Survey Activity"
    )

    @api.model
    def create(self, vals):
        """Override create method to create site survey activity if needed."""
        res = super(ResCompany, self).create(vals)
        if res.dynamic_stages_in_crm:
            survey_activity = self.env['mail.activity.type'].create({
                "company_id": res.id,
                'res_model': 'crm.lead',
                'name': 'Site Survey',
                "is_site_survey": True
            })
            res.write({"site_survey_activity_id": survey_activity.id})
        return res

    @api.onchange('dynamic_stages_in_crm')
    def onchange_dynamic_stages_in_crm(self):
        """Create activity type if dynamic_stages_in_crm is True."""
        if self.dynamic_stages_in_crm and not self.site_survey_activity_id:
            survey_activity = self.env['mail.activity.type'].create({
                "company_id": self._origin.id,
                'res_model': 'crm.lead',
                'name': 'Site Survey',
                "is_site_survey": True,
            })
            print("survey_activity",survey_activity)
            self.site_survey_activity_id = survey_activity.id
