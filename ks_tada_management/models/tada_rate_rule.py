from odoo import models, fields


class TadaRateRule(models.Model):
    _name = "ks.tada.rate.rule"
    _description = "TADA Rate Rule"
    _order = "travel_category, name"

    name = fields.Char(string="Rule Name", required=True)
    travel_category = fields.Selection([
        ("residential", "Internal Team Travel"),
        ("stakeholder", "Stakeholder / Government"),
        ("local_vehicle", "Local Travel — With Vehicle"),
        ("local_no_vehicle", "Local Travel — Without Vehicle"),
        ("full_board", "Full-Board Package"),
    ], string="Travel Category", required=True)

    rate_per_day = fields.Float(string="Rate per Day (NPR)", default=0.0)
    rate_per_km = fields.Float(string="Rate per KM (NPR)", default=0.0)
    first_last_day_rate = fields.Float(string="First / Last Day Rate (NPR)", default=0.0)
    full_board_percent = fields.Float(string="Full-Board % of Base", default=0.0)
    notes = fields.Text(string="Notes")

    active = fields.Boolean(default=True)
