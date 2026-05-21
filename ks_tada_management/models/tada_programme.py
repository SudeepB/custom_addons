from odoo import models, fields


class TadaProgramme(models.Model):
    _name = "ks.tada.programme"
    _description = "TADA Programme / Project"
    _order = "name"

    name = fields.Char(string="Programme / Project Name", required=True)
    purpose = fields.Char(string="Default Purpose of Travel")
    default_activity_code = fields.Char(string="Default Activity Code")
    notes = fields.Text(string="Notes")
    active = fields.Boolean(default=True)
