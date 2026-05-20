from odoo import models, fields


class TadaBill(models.Model):
    _name = "ks.tada.bill"
    _description = "TADA Bill"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )
    bill_amount = fields.Float(string="Bill Amount")
    bill_attachment = fields.Binary(string="Bill File")
    bill_attachment_name = fields.Char(string="Filename")