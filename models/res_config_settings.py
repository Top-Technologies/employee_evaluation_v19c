from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    eval_md_user_id = fields.Many2one(
        'res.users',
        string="Managing Director",
        domain="[('share', '=', False)]",
        help="Default Managing Director for employee evaluations."
    )
    eval_od_user_id = fields.Many2one(
        'res.users',
        string="Operations Director",
        domain="[('share', '=', False)]",
        help="Default Operations Director for employee evaluations."
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    eval_md_user_id = fields.Many2one(
        'res.users',
        related='company_id.eval_md_user_id',
        readonly=False,
        string="Managing Director",
        domain="[('share', '=', False)]",
        help="Select the Managing Director who will approve employee evaluations."
    )
    eval_od_user_id = fields.Many2one(
        'res.users',
        related='company_id.eval_od_user_id',
        readonly=False,
        string="Operations Director",
        domain="[('share', '=', False)]",
        help="Select the Operations Director who will approve employee evaluations."
    )
