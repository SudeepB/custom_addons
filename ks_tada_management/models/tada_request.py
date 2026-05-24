from odoo import models, fields, api
from odoo.exceptions import AccessError, ValidationError


class TadaRequest(models.Model):
    _name = "ks.tada.request"
    _description = "TADA Request"
    _inherit = ["mail.thread"]

    name = fields.Char(default="New", readonly=True)
    employee_id = fields.Many2one("hr.employee", required=True)

    # Computed readonly info pulled from the linked employee
    employee_designation = fields.Char(
        string="Designation",
        compute="_compute_employee_info",
        store=True,
    )
    employee_department = fields.Char(
        string="Department / Team",
        compute="_compute_employee_info",
        store=True,
    )

    @api.depends("employee_id")
    def _compute_employee_info(self):
        for rec in self:
            rec.employee_designation = rec.employee_id.job_id.name or ""
            rec.employee_department = rec.employee_id.department_id.name or ""

    @api.model
    def default_get(self, fields_list):
        """Pre-fill employee from the logged-in user's linked employee record."""
        res = super().default_get(fields_list)
        if "employee_id" in fields_list:
            employee = self.env["hr.employee"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            if employee:
                res["employee_id"] = employee.id
        return res

    # kept for backward compat / single-type quick entry
    travel_type = fields.Selection([
        ("residential", "Internal Team Travel"),
        ("stakeholder", "Stakeholder/Government"),
        ("local", "Local Travel"),
    ], string="Primary Travel Type")

    from_date = fields.Date()
    to_date = fields.Date()
    destination = fields.Char()
    purpose_of_travel = fields.Char(string="Purpose of Travel")
    project_title = fields.Char(string="Project / Programme")

    programme_id = fields.Many2one(
        "ks.tada.programme",
        string="Programme / Project",
    )

    @api.onchange("programme_id")
    def _onchange_programme(self):
        if self.programme_id:
            self.purpose_of_travel = self.programme_id.purpose
            self.project_title = self.programme_id.name

    # ── Multiple travel type lines ──────────────────────────────────────────
    travel_line_ids = fields.One2many(
        "ks.tada.travel.line",
        "request_id",
        string="Travel Lines",
    )

    travel_lines_amount = fields.Float(
        string="Travel Lines Total (NPR)",
        compute="_compute_travel_lines_amount",
        store=True,
    )

    @api.depends("travel_line_ids.line_amount")
    def _compute_travel_lines_amount(self):
        for rec in self:
            rec.travel_lines_amount = sum(rec.travel_line_ids.mapped("line_amount"))

    # ── Traveller groups (rate-rule based) ──────────────────────────────────
    traveller_ids = fields.One2many(
        "ks.tada.traveller",
        "request_id",
        string="Traveller Groups",
    )

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
        string="Bills",
    )

    itinerary_ids = fields.One2many(
        "ks.tada.itinerary",
        "request_id",
        string="Travel Itinerary",
    )
    advance_ids = fields.One2many(
        "ks.tada.advance",
        "request_id",
        string="Advance Requests",
    )

    submitted_by = fields.Many2one("res.users", string="Submitted By", readonly=True)
    approved_by = fields.Many2one("res.users", string="Approved By", readonly=True)

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

    total_advance = fields.Float(
        string="Total Advance Requested (NPR)",
        compute="_compute_total_advance",
        store=True,
    )

    @api.depends("advance_ids.advance_amount")
    def _compute_total_advance(self):
        for rec in self:
            rec.total_advance = sum(rec.advance_ids.mapped("advance_amount"))

    is_admin = fields.Boolean(
        string="Is Admin",
        compute="_compute_is_admin",
    )

    @api.depends_context("uid")
    def _compute_is_admin(self):
        is_admin = self.env.user.has_group("base.group_system")
        for rec in self:
            rec.is_admin = is_admin

    # -------------------------
    # Sequence
    # -------------------------
    @api.model
    def create(self, vals):
        if isinstance(vals, list):
            for v in vals:
                if isinstance(v, dict) and v.get("name", "New") == "New":
                    v["name"] = self.env["ir.sequence"].next_by_code("ks.tada.request") or "New"
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
        "bill_line_ids.bill_attachment_name",
        "from_date",
        "to_date",
        "traveller_ids.subtotal",
        "traveller_ids.rate_rule_id",
        "traveller_ids.count",
        "travel_line_ids.line_amount",
        "travel_line_ids.programme_id",
    )
    def _compute_amount(self):
        for rec in self:
            amount = 0.0
            settings = self.env["ks.tada.settings"].search([], limit=1)
            breakdown_lines = []

            # ── Travel lines (multi-type) ──
            if rec.travel_line_ids:
                breakdown_lines.append("Travel Lines:")
                for tl in rec.travel_line_ids:
                    ttype = dict(tl._fields["travel_type"].selection).get(tl.travel_type, tl.travel_type)
                    prog = tl.programme_id.name if tl.programme_id else ""
                    date_range = ""
                    if tl.from_date and tl.to_date:
                        date_range = f" ({tl.from_date.strftime('%d/%m')}–{tl.to_date.strftime('%d/%m')})"
                    prog_str = f" [{prog}]" if prog else ""
                    breakdown_lines.append(
                        f"  {ttype}{date_range}{prog_str} ×{tl.num_people}: NPR {tl.line_amount:.2f}"
                    )
                    if tl.breakdown:
                        breakdown_lines.append(f"    {tl.breakdown}")
                tl_total = sum(rec.travel_line_ids.mapped("line_amount"))
                breakdown_lines.append(f"  Travel Lines Total: NPR {tl_total:.2f}")
                amount += tl_total

            # ── Legacy single travel_type (only if no travel lines) ──
            elif rec.travel_type:
                days = 1
                if rec.from_date and rec.to_date:
                    delta = (rec.to_date - rec.from_date).days
                    days = max(1, delta + 1)

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
                        breakdown_lines.append(
                            f"Full-Board ({days}d × NPR {fb_base:.2f} @ {fb_percent:.2f}%): NPR {amount:.2f}"
                        )
                    else:
                        fl_days = 1 if days == 1 else 2
                        mid_days = max(0, days - 2)
                        fl_total = fl_rate * fl_days
                        mid_total = base_day * mid_days
                        breakdown_lines.append(f"First/Last days ({fl_days} × NPR {fl_rate:.2f}): NPR {fl_total:.2f}")
                        if mid_days:
                            breakdown_lines.append(f"Middle days ({mid_days} × NPR {base_day:.2f}): NPR {mid_total:.2f}")
                        amount = fl_total + mid_total

                elif rec.travel_type == "local":
                    if rec.with_vehicle:
                        rate_km = settings.rate_local_per_km if settings else 20.0
                        amount = rec.km_travelled * rate_km
                        breakdown_lines.append(f"Local ({rec.km_travelled}km × NPR {rate_km:.2f}): NPR {amount:.2f}")
                    else:
                        amount = rec.bill_amount or 0.0
                        breakdown_lines.append(f"Bill amount: NPR {amount:.2f}")

                elif rec.travel_type == "stakeholder":
                    rate = settings.rate_stakeholder if settings else 1600.0
                    amount = rate * days
                    breakdown_lines.append(f"Stakeholder ({days}d × NPR {rate:.2f}): NPR {amount:.2f}")

            # ── Traveller groups (rate-rule based) ──
            if rec.traveller_ids:
                trav_total = sum(rec.traveller_ids.mapped("subtotal"))
                breakdown_lines.append("─" * 30)
                breakdown_lines.append("Traveller Groups:")
                for t in rec.traveller_ids:
                    cat_label = dict(t._fields["member_category"].selection).get(
                        t.member_category, t.member_category or ""
                    )
                    breakdown_lines.append(
                        f"  [{cat_label}] {t.rate_rule_id.name} ×{t.count} ({t.days}d): NPR {t.subtotal:.2f}"
                    )
                breakdown_lines.append(f"  Travellers Total: NPR {trav_total:.2f}")
                amount += trav_total

            # ── Bill attachments ──
            if rec.bill_line_ids:
                breakdown_lines.append("─" * 30)
                breakdown_lines.append("Bill Attachments:")
                for line in rec.bill_line_ids:
                    breakdown_lines.append(
                        f"  {line.bill_attachment_name or 'Unnamed'}: NPR {line.bill_amount:.2f}"
                    )
                breakdown_lines.append(f"  Bills Total: NPR {rec.bill_amount:.2f}")

            breakdown_lines.append("─" * 30)
            breakdown_lines.append(f"Total Applied Amount: NPR {amount:.2f}")
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
            rec.approval_log = (
                f"{current_log}{message} by {self.env.user.name} on {fields.Datetime.now()}\n"
            )

    def action_submit(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError("Only draft requests can be submitted.")
            rec.state = "submitted"
            rec.submitted_by = self.env.user
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
            rec.approved_by = self.env.user
            rec._append_approval_log("Approved")

    def action_reject(self):
        self._require_admin()
        for rec in self:
            if rec.state not in ("submitted", "approved"):
                raise ValidationError("Only submitted or approved requests can be rejected.")
            rec.state = "rejected"
            rec._append_approval_log("Rejected")

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_print_taf(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Print TADA",
            "res_model": "ks.tada.print.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
            },
        }
