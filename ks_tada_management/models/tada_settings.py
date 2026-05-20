from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TadaSettings(models.Model):
    _name = "ks.tada.settings"
    _description = "TADA Rate Settings"

    name = fields.Char(default="TADA Settings", required=True)

    rate_residential_vehicle = fields.Float(
        string="Residential Rate with Vehicle",
        default=1500,
        groups="base.group_system",
    )
    rate_residential_no_vehicle = fields.Float(
        string="Residential Rate without Vehicle",
        default=2500,
        groups="base.group_system",
    )
    rate_first_last_day = fields.Float(
        string="First/Last Day Rate",
        default=2500,
        groups="base.group_system",
    )
    rate_full_board_base = fields.Float(
        string="Full Board Base Rate",
        default=2500,
        groups="base.group_system",
    )
    full_board_percent = fields.Float(
        string="Full Board %",
        default=20,
        groups="base.group_system",
    )
    rate_stakeholder = fields.Float(
        string="Stakeholder Rate",
        default=1600,
        groups="base.group_system",
    )
    rate_local_per_km = fields.Float(
        string="Local Travel Rate per KM",
        default=20,
        groups="base.group_system",
    )

    @api.constrains("name")
    def _check_singleton(self):
        if self.search_count([]) > 1:
            raise ValidationError("Only one TADA settings record is allowed.")
