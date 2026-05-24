from odoo import models, fields


class TadaItinerary(models.Model):
    _name = "ks.tada.itinerary"
    _description = "TADA Travel Itinerary"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )
    date = fields.Date(string="Date")

    programme_id = fields.Many2one(
        "ks.tada.programme",
        string="Programme / Project",
    )

    activity_type = fields.Selection([
        ("travel", "Travel"),
        ("workshop", "Workshop"),
        ("programme", "Programme / Meeting"),
        ("field_visit", "Field Visit"),
        ("other", "Other"),
    ], string="Activity Type", default="travel")

    location = fields.Char(string="Location / Venue")
    travel_from = fields.Char(string="From")
    travel_to = fields.Char(string="To")
    mode_of_transport = fields.Char(string="Mode of Transport")
    remarks = fields.Char(string="Remarks")
