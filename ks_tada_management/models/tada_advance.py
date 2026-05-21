from odoo import models, fields


class TadaAdvance(models.Model):
    _name = "ks.tada.advance"
    _description = "TADA Advance Request"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )
    activity_code = fields.Char(string="Activity Code")
    budget_line_item = fields.Char(string="Budget Line Item")
    advance_amount = fields.Float(string="Advance (A)")
    settled_expenses = fields.Float(string="Settled Expenses")
    remarks = fields.Char(string="Remarks")
