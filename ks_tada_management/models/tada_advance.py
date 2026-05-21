from odoo import models, fields, api


class TadaAdvance(models.Model):
    _name = "ks.tada.advance"
    _description = "TADA Advance Request"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )

    # ── Per-day advance fields ──────────────────────────────────────────────
    date = fields.Date(string="Date")

    member_category = fields.Selection([
        ("internal", "Internal Team Member"),
        ("government", "Government Official"),
        ("other", "Other"),
    ], string="Member Category", default="internal")

    member_count = fields.Integer(string="No. of Members", default=1)

    rate_rule_id = fields.Many2one(
        "ks.tada.rate.rule",
        string="Rate Rule",
        domain="[('travel_category', 'in', ['residential', 'stakeholder', 'full_board', 'local_vehicle', 'local_no_vehicle'])]",
    )

    days = fields.Integer(string="Days", default=1)
    km = fields.Float(string="KM (if applicable)", default=0.0)

    # ── Legacy / financial fields ───────────────────────────────────────────
    activity_code = fields.Char(string="Activity Code")
    budget_line_item = fields.Char(string="Budget Line Item")

    advance_amount = fields.Float(
        string="Advance (A)",
        compute="_compute_advance_amount",
        store=True,
    )
    settled_expenses = fields.Float(string="Settled Expenses")

    remarks = fields.Char(
        string="Remarks",
        compute="_compute_advance_amount",
        store=True,
    )

    # ── Computation ─────────────────────────────────────────────────────────
    @api.depends("member_category", "member_count", "rate_rule_id", "days", "km", "date")
    def _compute_advance_amount(self):
        for rec in self:
            rule = rec.rate_rule_id
            count = max(1, rec.member_count or 1)
            days = max(1, rec.days or 1)
            km = rec.km or 0.0
            date_str = str(rec.date) if rec.date else "N/A"

            category_label = dict(rec._fields["member_category"].selection).get(
                rec.member_category, rec.member_category or "N/A"
            )

            if not rule:
                rec.advance_amount = 0.0
                rec.remarks = f"[{date_str}] {category_label} x{count} — No rate rule selected"
                continue

            cat = rule.travel_category

            if cat == "residential":
                if days <= 1:
                    per_person = rule.first_last_day_rate
                    calc_detail = f"1 day (first/last rate) x NPR {rule.first_last_day_rate:.2f}"
                else:
                    first_last = rule.first_last_day_rate * 2
                    middle = rule.rate_per_day * max(0, days - 2)
                    per_person = first_last + middle
                    calc_detail = (
                        f"2 days (first/last) x NPR {rule.first_last_day_rate:.2f}"
                        f" + {max(0, days - 2)} middle day(s) x NPR {rule.rate_per_day:.2f}"
                    )
                total = per_person * count
                rec.advance_amount = total
                rec.remarks = (
                    f"[{date_str}] {category_label} x{count} | {rule.name} | "
                    f"{calc_detail} = NPR {per_person:.2f}/person | Total: NPR {total:.2f}"
                )

            elif cat == "full_board":
                per_person = rule.rate_per_day * (rule.full_board_percent / 100.0) * days
                total = per_person * count
                rec.advance_amount = total
                rec.remarks = (
                    f"[{date_str}] {category_label} x{count} | {rule.name} | "
                    f"Full-Board: NPR {rule.rate_per_day:.2f} x {rule.full_board_percent:.0f}% x {days}d"
                    f" = NPR {per_person:.2f}/person | Total: NPR {total:.2f}"
                )

            elif cat == "stakeholder":
                per_person = rule.rate_per_day * days
                total = per_person * count
                rec.advance_amount = total
                rec.remarks = (
                    f"[{date_str}] {category_label} x{count} | {rule.name} | "
                    f"NPR {rule.rate_per_day:.2f}/day x {days}d = NPR {per_person:.2f}/person | Total: NPR {total:.2f}"
                )

            elif cat == "local_vehicle":
                per_person = rule.rate_per_km * km
                total = per_person * count
                rec.advance_amount = total
                rec.remarks = (
                    f"[{date_str}] {category_label} x{count} | {rule.name} | "
                    f"NPR {rule.rate_per_km:.2f}/km x {km:.1f}km = NPR {per_person:.2f}/person | Total: NPR {total:.2f}"
                )

            elif cat == "local_no_vehicle":
                per_person = rule.rate_per_day
                total = per_person * count
                rec.advance_amount = total
                rec.remarks = (
                    f"[{date_str}] {category_label} x{count} | {rule.name} | "
                    f"NPR {rule.rate_per_day:.2f}/person | Total: NPR {total:.2f}"
                )

            else:
                rec.advance_amount = 0.0
                rec.remarks = f"[{date_str}] {category_label} x{count} — Unknown category"
