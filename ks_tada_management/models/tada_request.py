from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError

class TadaRequest(models.Model):
    _name = "ks.tada.request"
    _description = "TADA Request"
    _inherit = ["mail.thread"]

    name = fields.Char(default="New", readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True)

    travel_type = fields.Selection([
        ("residential", "Internal Team Travel"),
        ("stakeholder", "Stakeholder/Government"),
        ("local", "Local Travel"),
    ], required=True)

    from_date = fields.Date()
    to_date = fields.Date()
    destination = fields.Char()

    with_vehicle = fields.Boolean()
    km_travelled = fields.Float()

    bill_amount = fields.Float(
        string="Bill Amount",
        compute="_compute_bill_amount",
        store=True,
    )
    bill_line_ids = fields.One2many(
        "ks.tada.bill",
        "request_id",
        string="Bills"
    )

    full_board = fields.Boolean()
    box_material = fields.Boolean()

    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ], default="draft", tracking=True)

    amount = fields.Float(compute="_compute_amount", store=True)
    amount_breakdown = fields.Text(compute="_compute_amount", store=True)
    approval_log = fields.Text(string="Approval Log", readonly=True)

    # -------------------------
    # Sequence
    # -------------------------
    @api.model
    def create(self, vals):
        # Support both single and bulk create calls. Odoo may call create
        # with a list of dicts when saving from the web client.
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, dict) and v.get("name", "New") == "New":
                    v["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
                elif isinstance(v, (list, tuple)) and len(v) and isinstance(v[0], dict) and v[0].get("name", "New") == "New":
                    v[0]["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
            return super().create(vals)

        if isinstance(vals, dict) and vals.get("name", "New") == "New":
            vals["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
        return super().create(vals)

    @api.depends("bill_line_ids.bill_amount")
    def _compute_bill_amount(self):
        for rec in self:
            rec.bill_amount = sum(rec.bill_line_ids.mapped("bill_amount"))

    # -------------------------
    # Computation Logic
    # -------------------------
    @api.depends(
        "travel_type",
        "with_vehicle",
        "km_travelled",
        "full_board",
        "bill_amount",
        "bill_line_ids.bill_amount",
        "from_date",
        "to_date",
    )
    def _compute_amount(self):
        for rec in self:
            amount = 0
            # load settings singleton (if missing, fall back to defaults)
            settings = self.env["ks.tada.settings"].search([], limit=1)

            # compute travel days (inclusive)
            days = 1
            if rec.from_date and rec.to_date:
                try:
                    d0 = fields.Date.from_string(rec.from_date)
                    d1 = fields.Date.from_string(rec.to_date)
                    delta = (d1 - d0).days
                    days = max(1, delta + 1)
                except Exception:
                    days = 1

            breakdown_lines = []

            # Residential Travel: per-day base rate with higher first/last day rates
            if rec.travel_type == "residential":
                if settings:
                    base_day = settings.rate_residential_vehicle if rec.with_vehicle else settings.rate_residential_no_vehicle
                    fl_rate = settings.rate_first_last_day
                else:
                    base_day = 1500.0 if rec.with_vehicle else 2500.0
                    fl_rate = 2500.0

                if rec.full_board:
                    fb_base = settings.rate_full_board_base if settings else 2500.0
                    fb_percent = settings.full_board_percent if settings else 20.0
                    amount = fb_base * (fb_percent / 100.0) * days
                    breakdown_lines.append(f"Full-Board Package ({days} day(s) x {fb_base:.2f} @ {fb_percent:.2f}%): {amount:.2f}")
                else:
                    if days == 1:
                        first_last_days = 1
                        middle_days = 0
                    else:
                        first_last_days = 2
                        middle_days = max(0, days - 2)

                    first_last_total = fl_rate * first_last_days
                    middle_total = base_day * middle_days
                    breakdown_lines.append(f"First/Last days ({first_last_days} x {fl_rate:.2f}): {first_last_total:.2f}")
                    if middle_days:
                        breakdown_lines.append(f"Middle days ({middle_days} x {base_day:.2f}): {middle_total:.2f}")
                    amount = first_last_total + middle_total

            # Local Travel
            elif rec.travel_type == "local":
                if rec.with_vehicle:
                    rate_km = settings.rate_local_per_km if settings else 20.0
                    km_total = rec.km_travelled * rate_km
                    breakdown_lines.append(f"Local travel ({rec.km_travelled} km x {rate_km:.2f}): {km_total:.2f}")
                    amount = km_total
                else:
                    bill_amount = rec.bill_amount or 0.0
                    breakdown_lines.append(f"Bill amount: {bill_amount:.2f}")
                    amount = bill_amount

            # Stakeholder/Gov
            elif rec.travel_type == "stakeholder":
                stake_rate = settings.rate_stakeholder if settings else 1600.0
                amount = stake_rate * days
                breakdown_lines.append(f"Stakeholder rate ({days} day(s) x {stake_rate:.2f}): {amount:.2f}")

            # Build breakdown text and final amount
            breakdown_lines.append(f"Total: {amount:.2f}")
            rec.amount = amount
            rec.amount_breakdown = "\n".join(breakdown_lines)

    # -------------------------
    # Workflow Actions
    # -------------------------
    def _require_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError("Only administrators can approve or reject TADA requests.")

    def _append_approval_log(self, message):
        for rec in self:
            current_log = rec.approval_log or ""
            rec.approval_log = f"{current_log}{message} by {self.env.user.name} on {fields.Datetime.now()}\n"

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError("Only draft requests can be submitted.")
            rec.state = "submitted"
            rec._append_approval_log("Submitted")

    def action_finance_approve(self):
        for rec in self:
            rec.state = "approved"

    def action_approve(self):
        self._require_admin()
        for rec in self:
            if rec.state != "submitted":
                raise ValidationError("Only submitted requests can be approved.")
            rec.state = "approved"
            rec._append_approval_log("Approved")

    def action_reject(self):
        self._require_admin()
        for rec in self:
            if rec.state != "submitted":
                raise ValidationError("Only submitted requests can be rejected.")
            rec.state = "rejected"
            rec._append_approval_log("Rejected")

    def action_draft(self):
        for rec in self:
            rec.state = "draft"