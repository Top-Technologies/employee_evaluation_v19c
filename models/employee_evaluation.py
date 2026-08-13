from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError
import logging
from . import ethiopian_calendar

_logger = logging.getLogger(__name__)


class EmployeeEvaluation(models.Model):
    _name = 'employee.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Evaluation'
    _order = 'create_date desc'

    # ==================== RATING SELECTION ====================
    RATING_SELECTION = [
        ('5', '5)'), ('4', '4)'), ('3', '3)'),
        ('2', '2)'), ('1', '1)'), ('NA', 'NA)')
    ]

    # ==================== BASIC FIELDS ====================
    name = fields.Char(
        string="Reference",
        compute='_compute_name',
        store=True,
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    md_user_id = fields.Many2one(
        'res.users',
        string='Managing Director',
        related='company_id.eval_md_user_id',
        store=True,
        readonly=True,
        help="Managing Director configured in Settings"
    )

    od_user_id = fields.Many2one(
        'res.users',
        string='Operations Director',
        related='company_id.eval_od_user_id',
        store=True,
        readonly=True,
        help="Operations Director configured in Settings"
    )

    evaluation_type = fields.Selection(
        [
            ('two_months', '2 Months Evaluation'),
            ('six_months', '6 Months Evaluation'),
        ],
        string='Evaluation Type',
        required=True,
        default='two_months',
        tracking=True,
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        tracking=True,
    )

    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        related='employee_id.department_id',
        store=True,
        readonly=True,
        compute_sudo=True
    )

    job_id = fields.Many2one(
        'hr.job',
        string="Job Position",
        related='employee_id.job_id',
        store=True,
        readonly=True,
        compute_sudo=True
    )

    manager_id = fields.Many2one(
        'hr.employee',
        string="Direct Manager",
        related='employee_id.parent_id',
        store=True,
        readonly=True,
        compute_sudo=True
    )

    branch = fields.Many2many(
        'hr.employee.category',
        string="Tags",
        related='employee_id.category_ids',
        readonly=True,
        compute_sudo=True
    )

    # ==================== DATE FIELDS ====================
    start_date = fields.Date(string="Period Start", default=fields.Date.today)
    end_date = fields.Date(string="Period End", default=fields.Date.today)
    evaluation_date = fields.Date(string='Evaluation Date', readonly=True)

    # ==================== EMPLOYEE TYPE ====================
    eval_employee_type = fields.Selection(
        related='employee_id.emp_eval_type',
        selection=[
            ('supervisor', 'Supervisor'),
            ('standard', 'Employee'),
        ],
        string='Employee Type',
        store=True,
        readonly=True,
        compute_sudo=True
    )

    # ==================== WORKFLOW STATE ====================
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('manager_approved', 'Manager Approved'),
            ('md_approved', 'MD Approved'),
            ('od_approved', 'OD Approved'),
            ('employee_reviewed', 'Employee Reviewed'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )

    # ==================== COMMENT FIELDS ====================
    manager_comment = fields.Text(string="Direct Manager's Feedback")
    md_comment = fields.Text(string="Managing Director's Comment")
    od_comment = fields.Text(string="Operations Director's Comment")
    employee_comment = fields.Text(string="Employee's Remarks")

    # ==================== COMPUTED/HELPER FIELDS ====================
    total_score = fields.Float(
        string="Total Score",
        compute="_compute_total_score",
        store=True
    )

    is_self = fields.Boolean(compute='_compute_is_self')
    is_manager = fields.Boolean(compute='_compute_is_manager')
    is_md = fields.Boolean(compute='_compute_is_md')
    is_od = fields.Boolean(compute='_compute_is_od')

    # ==================== QUESTION FIELDS (q1-q25) ====================
    q1 = fields.Selection(RATING_SELECTION, string="Q1")
    q2 = fields.Selection(RATING_SELECTION, string="Q2")
    q3 = fields.Selection(RATING_SELECTION, string="Q3")
    q4 = fields.Selection(RATING_SELECTION, string="Q4")
    q5 = fields.Selection(RATING_SELECTION, string="Q5")
    q6 = fields.Selection(RATING_SELECTION, string="Q6")
    q7 = fields.Selection(RATING_SELECTION, string="Q7")
    q8 = fields.Selection(RATING_SELECTION, string="Q8")
    q9 = fields.Selection(RATING_SELECTION, string="Q9")
    q10 = fields.Selection(RATING_SELECTION, string="Q10")
    q11 = fields.Selection(RATING_SELECTION, string="Q11")
    q12 = fields.Selection(RATING_SELECTION, string="Q12")
    q13 = fields.Selection(RATING_SELECTION, string="Q13")
    q14 = fields.Selection(RATING_SELECTION, string="Q14")
    q15 = fields.Selection(RATING_SELECTION, string="Q15")
    q16 = fields.Selection(RATING_SELECTION, string="Q16")
    q17 = fields.Selection(RATING_SELECTION, string="Q17")
    q18 = fields.Selection(RATING_SELECTION, string="Q18")
    q19 = fields.Selection(RATING_SELECTION, string="Q19")
    q20 = fields.Selection(RATING_SELECTION, string="Q20")
    q21 = fields.Selection(RATING_SELECTION, string="Q21")
    q22 = fields.Selection(RATING_SELECTION, string="Q22")
    q23 = fields.Selection(RATING_SELECTION, string="Q23")
    q24 = fields.Selection(RATING_SELECTION, string="Q24")
    q25 = fields.Selection(RATING_SELECTION, string="Q25")

    # ==================== COMPUTED METHODS ====================

    @api.depends('employee_id', 'evaluation_type')
    def _compute_name(self):
        type_labels = dict(self._fields['evaluation_type'].selection)
        for rec in self:
            if rec.employee_id and rec.evaluation_type:
                rec.name = f"{rec.employee_id.sudo().name} - {type_labels.get(rec.evaluation_type, '')}"
            else:
                rec.name = "New Evaluation"

    @api.depends_context('uid')
    @api.depends('employee_id')
    def _compute_is_self(self):
        current_user_id = self.env.user.id
        for rec in self:
            emp_user = rec.employee_id.sudo().user_id
            rec.is_self = bool(emp_user and emp_user.id == current_user_id)

    @api.depends_context('uid')
    @api.depends('employee_id', 'employee_id.parent_id')
    def _compute_is_manager(self):
        user = self.env.user
        is_hr = user.has_group('employee_evaluation_v19c.group_evaluation_hr')
        is_manager_group = user.has_group('employee_evaluation_v19c.group_evaluation_manager')
        for rec in self:
            mgr_user = rec.employee_id.sudo().parent_id.sudo().user_id
            rec.is_manager = is_hr or is_manager_group or bool(mgr_user and mgr_user.id == user.id)

    @api.depends_context('uid')
    @api.depends('md_user_id')
    def _compute_is_md(self):
        user = self.env.user
        is_hr = user.has_group('employee_evaluation_v19c.group_evaluation_hr')
        is_md_group = user.has_group('employee_evaluation_v19c.group_evaluation_md')
        for rec in self:
            rec.is_md = is_hr or is_md_group or bool(rec.md_user_id and rec.md_user_id.id == user.id)

    @api.depends_context('uid')
    @api.depends('od_user_id')
    def _compute_is_od(self):
        user = self.env.user
        is_hr = user.has_group('employee_evaluation_v19c.group_evaluation_hr')
        is_od_group = user.has_group('employee_evaluation_v19c.group_evaluation_od')
        for rec in self:
            rec.is_od = is_hr or is_od_group or bool(rec.od_user_id and rec.od_user_id.id == user.id)

    @api.depends(
        'evaluation_type', 'eval_employee_type',
        'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10',
        'q11', 'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20',
        'q21', 'q22', 'q23', 'q24', 'q25'
    )
    def _compute_total_score(self):
        for rec in self:
            total = 0
            if rec.evaluation_type == 'two_months':
                for i in range(1, 9):
                    val = getattr(rec, f'q{i}')
                    if val and val.isdigit():
                        total += int(val)
            elif rec.evaluation_type == 'six_months':
                if rec.eval_employee_type == 'standard':
                    for i in range(1, 11):
                        val = getattr(rec, f'q{i}')
                        if val and val.isdigit():
                            total += int(val)
                elif rec.eval_employee_type == 'supervisor':
                    for i in range(11, 26):
                        val = getattr(rec, f'q{i}')
                        if val and val.isdigit():
                            total += int(val)
            rec.total_score = total

    # ==================== VALIDATION ====================

    def _validate_evaluation_submission(self):
        """Validate that no duplicate evaluation exists for the same employee+type+period."""
        for rec in self:
            if rec.employee_id and rec.start_date and rec.end_date:
                domain = [
                    ('id', '!=', rec.id),
                    ('employee_id', '=', rec.employee_id.id),
                    ('evaluation_type', '=', rec.evaluation_type),
                    ('start_date', '<=', rec.end_date),
                    ('end_date', '>=', rec.start_date),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        "An evaluation of this type already exists for this "
                        "employee within the specified period."
                    )

    # ==================== WORKFLOW ACTIONS ====================

    def action_manager_approve(self):
        """Step 1: Direct Manager submits the evaluation to MD."""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError("This action is only allowed from Draft state.")

        if not self.is_manager:
            raise AccessError("Only the Direct Manager or HR Manager can submit this evaluation.")

        self._validate_evaluation_submission()
        self.state = 'manager_approved'

        try:
            partners = []
            if self.md_user_id and self.md_user_id.partner_id:
                partners.append(self.md_user_id.partner_id.id)
            else:
                md_group = self.env.ref('employee_evaluation_v19c.group_evaluation_md')
                partners = md_group.users.mapped('partner_id').ids

            self.message_post(
                body=f"Evaluation for {self.employee_id.name} submitted by "
                     f"{self.env.user.name}. Waiting for Managing Director review.",
                partner_ids=partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send notification to MD: %s", str(e))
        return True

    def action_md_approve(self):
        """Step 2: Managing Director approves and forwards to OD."""
        self.ensure_one()
        if self.state != 'manager_approved':
            raise ValidationError("This action is only allowed from Manager Approved state.")

        if not self.is_md:
            raise AccessError(
                f"Only the designated Managing Director ({self.md_user_id.name if self.md_user_id else 'configured in Settings'}) "
                "or HR Manager can approve at this stage."
            )

        self.state = 'md_approved'

        try:
            partners = []
            if self.od_user_id and self.od_user_id.partner_id:
                partners.append(self.od_user_id.partner_id.id)
            else:
                od_group = self.env.ref('employee_evaluation_v19c.group_evaluation_od')
                partners = od_group.users.mapped('partner_id').ids

            self.message_post(
                body=f"Evaluation for {self.employee_id.name} approved by Managing Director "
                     f"{self.env.user.name}. Waiting for Operations Director review.",
                partner_ids=partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send notification to OD: %s", str(e))
        return True

    def action_od_approve(self):
        """Step 3: Operations Director approves and forwards to Employee for review."""
        self.ensure_one()
        if self.state != 'md_approved':
            raise ValidationError("This action is only allowed from MD Approved state.")

        if not self.is_od:
            raise AccessError(
                f"Only the designated Operations Director ({self.od_user_id.name if self.od_user_id else 'configured in Settings'}) "
                "or HR Manager can approve at this stage."
            )

        self.state = 'od_approved'

        try:
            partners = []
            if self.employee_id.sudo().user_id:
                partners.append(self.employee_id.sudo().user_id.partner_id.id)
            self.message_post(
                body=f"Evaluation for {self.employee_id.name} has been reviewed by all directors. "
                     f"Employee review is now required.",
                partner_ids=partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send notification to employee: %s", str(e))
        return True

    def action_employee_review(self):
        """Step 4: Employee submits their remarks."""
        self.ensure_one()
        if self.state != 'od_approved':
            raise ValidationError("This action is only allowed from OD Approved state.")

        current_user = self.env.user
        is_hr = current_user.has_group('employee_evaluation_v19c.group_evaluation_hr')
        if not (self.is_self or is_hr):
            raise AccessError("Only the evaluated employee or HR Manager can submit this review.")

        if not self.employee_comment:
            raise ValidationError("Please provide your remarks before submitting.")

        self.state = 'employee_reviewed'

        try:
            hr_group = self.env.ref('employee_evaluation_v19c.group_evaluation_hr')
            hr_partners = hr_group.users.mapped('partner_id').ids
            self.message_post(
                body=f"Employee {self.employee_id.name} has submitted their review. "
                     f"Waiting for HR Manager final approval.",
                partner_ids=hr_partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send notification to HR: %s", str(e))
        return True

    def action_hr_approve(self):
        """Step 5: HR Manager gives final approval."""
        self.ensure_one()
        if self.state not in ('draft', 'manager_approved', 'md_approved',
                              'od_approved', 'employee_reviewed'):
            raise ValidationError("Cannot approve from the current state.")

        if not self.env.user.has_group('employee_evaluation_v19c.group_evaluation_hr'):
            raise AccessError("Only HR Managers can give final approval.")

        self.state = 'done'
        self.evaluation_date = fields.Date.today()

        try:
            partners = []
            if self.employee_id.sudo().user_id:
                partners.append(self.employee_id.sudo().user_id.partner_id.id)
            if self.employee_id.sudo().parent_id and self.employee_id.sudo().parent_id.sudo().user_id:
                partners.append(self.employee_id.sudo().parent_id.sudo().user_id.partner_id.id)

            self.message_post(
                body=f"Evaluation for {self.employee_id.name} has been approved and finalized by HR.",
                partner_ids=partners,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            _logger.warning("Failed to send final approval notification: %s", str(e))
        return True

    def action_reset_to_draft(self):
        """HR can reset an evaluation back to draft."""
        self.ensure_one()
        if not self.env.user.has_group('employee_evaluation_v19c.group_evaluation_hr'):
            raise AccessError("Only HR Managers can reset evaluations.")
        self.state = 'draft'
        self.message_post(
            body=f"Evaluation reset to Draft by {self.env.user.name}.",
            subtype_xmlid='mail.mt_comment'
        )
        return True

    def action_preview(self):
        """Print the evaluation report."""
        return self.env.ref(
            'employee_evaluation_v19c.action_report_employee_evaluation'
        ).report_action(self)

    # ==================== ETHIOPIAN DATE HELPER ====================

    def get_ethiopian_date_str(self, date_value):
        return ethiopian_calendar.format_ethiopian_date(date_value)
