from odoo import models, fields, api


class TadaTravelLine(models.Model):
    _name = "ks.tada.travel.line"
    _description = "TADA Travel Line"
    _order = "from_date, id"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
        ondelete="cascade",
    )

    programme_id = fields.Many2one(
        "ks.tada.programme",
        string="Programme / Project",
    )

    travel_type = fields.Selection([
        ("residential", "Internal Team Travel"),
        ("stakeholder", "Stakeholder / Government"),
        ("local", "Local Travel"),
    ], string="Travel Type", required=True)

    num_people = fields.Integer(string="No. of People", default=1)

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    # local travel extras
    with_vehicle = fields.Boolean(string="With Vehicle")
    km_travelled = fields.Float(string="KM Travelled")

    # residential extras
    full_board = fields.Boolean(string="Full-Board")

    line_amount = fields.Float(
        string="Amount (NPR)",
        compute="_compute_line_amount",
        store=True,
    )
    breakdown = fields.Char(
        string="Breakdown",
        compute="_compute_line_amount",
        store=True,
    )

    @api.depends(
        "travel_type", "num_people",
        "from_date", "to_date", "with_vehicle", "km_travelled", "full_board",
    )
    def _compute_line_amount(self):
        for rec in self:
            settings = rec.env["ks.tada.settings"].search([], limit=1)

            # days inclusive
            days = 1
            if rec.from_date and rec.to_date:
                delta = (rec.to_date - rec.from_date).days
                days = max(1, delta + 1)

            people = max(1, rec.num_people or 1)
            amount = 0.0
            detail = ""

            if rec.travel_type == "residential":
                if rec.full_board:
                    fb_base = settings.rate_full_board_base if settings else 2500.0
                    fb_pct = settings.full_board_percent if settings else 20.0
                    per_person = fb_base * (fb_pct / 100.0) * days
                    amount = per_person * people
                    detail = (
                        f"Full-Board {days}d × NPR {fb_base:.0f} @ {fb_pct:.0f}%"
                        f" = NPR {per_person:.0f}/person × {people} = NPR {amount:.0f}"
                    )
                else:
                    fl = settings.rate_first_last_day if settings else 2500.0
                    base = (settings.rate_residential_vehicle if rec.with_vehicle
                            else settings.rate_residential_no_vehicle) if settings else 1500.0
                    if days == 1:
                        per_person = fl
                        detail = f"1d (first/last) NPR {fl:.0f}/person"
                    else:
                        mid = max(0, days - 2)
                        per_person = fl * 2 + base * mid
                        detail = (
                            f"2 first/last × NPR {fl:.0f}"
                            + (f" + {mid} mid × NPR {base:.0f}" if mid else "")
                            + f" = NPR {per_person:.0f}/person"
                        )
                    amount = per_person * people
                    detail += f" × {people} = NPR {amount:.0f}"

            elif rec.travel_type == "stakeholder":
                rate = settings.rate_stakeholder if settings else 1600.0
                per_person = rate * days
                amount = per_person * people
                detail = (
                    f"NPR {rate:.0f}/day × {days}d = NPR {per_person:.0f}/person"
                    f" × {people} = NPR {amount:.0f}"
                )

            elif rec.travel_type == "local":
                if rec.with_vehicle:
                    rate_km = settings.rate_local_per_km if settings else 20.0
                    amount = rec.km_travelled * rate_km * people
                    detail = (
                        f"{rec.km_travelled:.1f}km × NPR {rate_km:.0f}/km"
                        f" × {people} = NPR {amount:.0f}"
                    )
                else:
                    amount = 0.0
                    detail = "No vehicle — bill-based (add in Bill Attachments)"

            rec.line_amount = amount
            rec.breakdown = detail
