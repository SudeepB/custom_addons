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

    # ── Per-day / activity fields ───────────────────────────────────────────
    date = fields.Date(string="Date")

    programme_id = fields.Many2one(
        "ks.tada.programme",
        string="Programme / Project",
    )

    member_category = fields.Selection([
        ("internal", "Internal Team Member"),
        ("government", "Government Official"),
        ("other", "Other"),
    ], string="Member Category", default="internal")

    member_count = fields.Integer(string="No. of Members", default=1)

    # ── Financial fields ────────────────────────────────────────────────────
    budget_line_item = fields.Char(string="Budget Line Item")

    advance_amount = fields.Float(string="Advance (NPR)")
    settled_expenses = fields.Float(string="Settled Expenses")

    # Large text field for calculation context / remarks
    remarks = fields.Text(string="Remarks / Calculation")
