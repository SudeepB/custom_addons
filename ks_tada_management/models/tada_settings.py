from odoo import models, fields, api


class TadaSettings(models.Model):
    _name = "ks.tada.settings"
    _description = "TADA Rate Settings"

    name = fields.Char(default="TADA Settings")

    rate_residential_vehicle = fields.Float(default=1500)
    rate_residential_no_vehicle = fields.Float(default=2500)
    rate_first_last_day = fields.Float(default=2500)
    rate_full_board_base = fields.Float(default=2500)
    full_board_percent = fields.Float(default=20)
    rate_stakeholder = fields.Float(default=1600)
    rate_local_per_km = fields.Float(default=20)

    # ---------------------------------------------------
    # SINGLETON ACCESS (SAFE)
    # ---------------------------------------------------

    @api.model
    def get_settings(self):
        """Always fetch single settings record"""
        record = self.search([], limit=1)
        if not record:
            record = self.create({})
        return record

    @api.model
    def create(self, vals):
        """Prevent multiple records safely"""
        if self.search_count([]) > 0:
            return self.search([], limit=1)
        return super().create(vals)