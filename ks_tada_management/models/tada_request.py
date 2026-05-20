from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError

class TadaRequest(models.Model):
    _name = "ks.tada.request"
    _description = "TADA Request"
    _inherit = ["mail.thread"]

    name = fields.Char(default="New", readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True)

    travel_type = fields.Selection([
        ("residential", "Residential Travel"),
        ("local", "Local Travel"),
        ("stakeholder", "Stakeholder/Government"),
    ], required=True)

    from_date = fields.Date()
    to_date = fields.Date()
    destination = fields.Char()

    with_vehicle = fields.Boolean()
    km_travelled = fields.Float()

    taxi_bill = fields.Float()

    full_board = fields.Boolean()
    first_last_day = fields.Boolean()
    box_material = fields.Boolean()

    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)

    amount = fields.Float(compute="_compute_amount", store=True)

    # -------------------------
    # Sequence
    # -------------------------
    @api.model
    def create(self, vals):
        # Support both single and bulk create calls. Odoo may call create
        # with a list of dicts when saving from the web client.
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, dict):
                    if v.get("name", "New") == "New":
                        v["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
                elif isinstance(v, (list, tuple)) and len(v) and isinstance(v[0], dict):
                    if v[0].get("name", "New") == "New":
                        v[0]["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
            return super().create(vals)

        if isinstance(vals, dict) and vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
        return super().create(vals)

    # -------------------------
    # Computation Logic
    # -------------------------
    @api.depends(
        "travel_type",
        "with_vehicle",
        "km_travelled",
        "full_board",
        "first_last_day",
        "taxi_bill"
    )
    def _compute_amount(self):
        for rec in self:
            amount = 0

            # Residential Travel
            if rec.travel_type == "residential":
                amount = 1500 if rec.with_vehicle else 2500

                if rec.first_last_day:
                    amount += 2500

            # Local Travel
            elif rec.travel_type == "local":
                if rec.with_vehicle:
                    amount = rec.km_travelled * 20
                else:
                    amount = rec.taxi_bill

            # Stakeholder/Gov
            elif rec.travel_type == "stakeholder":
                amount = 1600

            # Full board package override logic
            if rec.travel_type == "residential" and rec.full_board:
                amount = 500  # 20% of 2500

            rec.amount = amount

    # -------------------------
    # Workflow Actions
    # -------------------------
    def _require_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError("Only administrators can approve or reject TADA requests.")

    def action_submit(self):
        for rec in self:
            rec.state = "submitted"

    def action_finance_approve(self):
        for rec in self:
            rec.state = "approved"

    def action_approve(self):
        for rec in self:
            rec.state = "approved"

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"