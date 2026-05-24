from odoo import models, fields


class TadaPrintWizard(models.TransientModel):
    _name = "ks.tada.print.wizard"
    _description = "TADA Print Options"

    request_id = fields.Many2one(
        "ks.tada.request",
        string="TADA Request",
        required=True,
    )

    print_mode = fields.Selection([
        ("claim", "Claim Only (Applied Amount)"),
        ("advance", "Advance Request Only"),
        ("both", "Both (Claim + Advance)"),
    ], string="What to Print", default="both", required=True)

    def action_print(self):
        self.ensure_one()
        # Pass print_mode via report context so QWeb can read it from docs_ids context
        report = self.env.ref("ks_tada_management.action_report_tada_request")
        return report.with_context(
            print_mode=self.print_mode,
        ).report_action(self.request_id)
