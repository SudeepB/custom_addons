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
    travel_from = fields.Char(string="Travel From")
    travel_to = fields.Char(string="Travel To")
    mode_of_transport = fields.Char(string="Mode of Transportation")
    remarks = fields.Char(string="Remarks")
