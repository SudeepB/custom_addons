from odoo import models, fields, api
from odoo.exceptions import ValidationError


# Maximum allowed members per member category
CATEGORY_LIMITS = {
    "internal": 5,
    "government": 2,
    "other": 0,   # 0 = no limit
}

CATEGORY_LABELS = {
    "internal": "Internal Team Member",
    "government": "Government Official",
    "other": "Other",
}


class TadaTraveller(models.Model):
    _name = "ks.tada.traveller"
    _description = "TADA Traveller Group"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )

    # ── Member category with limits ─────────────────────────────────────────
    member_category = fields.Selection([
        ("internal", "Internal Team Member (max 5)"),
        ("government", "Government Official (max 2)"),
        ("other", "Other"),
    ], string="Member Category", default="internal", required=True)

    max_allowed = fields.Integer(
        string="Max Allowed",
        compute="_compute_max_allowed",
    )

    rate_rule_id = fields.Many2one(
        "ks.tada.rate.rule",
        string="Rate Rule",
        required=True,
    )
    travel_category = fields.Selection(
        related="rate_rule_id.travel_category",
        string="Travel Category",
        store=True,
    )
    count = fields.Integer(string="Number of People", default=1)
    days = fields.Integer(string="Days", default=1)
    km = fields.Float(string="KM (if applicable)", default=0.0)
    subtotal = fields.Float(
        string="Subtotal (NPR)",
        compute="_compute_subtotal",
        store=True,
    )
    notes = fields.Char(string="Remarks")

    @api.depends("member_category")
    def _compute_max_allowed(self):
        for rec in self:
            rec.max_allowed = CATEGORY_LIMITS.get(rec.member_category, 0)

    @api.constrains("member_category", "count")
    def _check_member_limit(self):
        for rec in self:
            limit = CATEGORY_LIMITS.get(rec.member_category, 0)
            if limit and rec.count > limit:
                label = CATEGORY_LABELS.get(rec.member_category, rec.member_category)
                raise ValidationError(
                    f"'{label}' category allows a maximum of {limit} member(s). "
                    f"You entered {rec.count}."
                )

    @api.depends("rate_rule_id", "count", "days", "km")
    def _compute_subtotal(self):
        for rec in self:
            rule = rec.rate_rule_id
            if not rule:
                rec.subtotal = 0.0
                continue

            cat = rule.travel_category
            if cat == "residential":
                if rec.days <= 1:
                    rec.subtotal = rule.first_last_day_rate * rec.count
                else:
                    first_last = rule.first_last_day_rate * 2
                    middle = rule.rate_per_day * max(0, rec.days - 2)
                    rec.subtotal = (first_last + middle) * rec.count

            elif cat == "full_board":
                rec.subtotal = (
                    rule.rate_per_day * (rule.full_board_percent / 100.0) * rec.days * rec.count
                )

            elif cat == "stakeholder":
                rec.subtotal = rule.rate_per_day * rec.days * rec.count

            elif cat == "local_vehicle":
                rec.subtotal = rule.rate_per_km * rec.km * rec.count

            elif cat == "local_no_vehicle":
                rec.subtotal = rule.rate_per_day * rec.count

            else:
                rec.subtotal = 0.0
