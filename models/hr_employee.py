from odoo import models, api, fields


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    evaluation_ids = fields.One2many(
        'employee.evaluation',
        'employee_id',
        string='Evaluations'
    )

    evaluation_count = fields.Integer(
        string='Evaluation Count',
        compute='_compute_evaluation_count',
    )

    emp_eval_type = fields.Selection(
        [
            ('supervisor', 'Supervisor/Manager'),
            ('standard', 'Employee'),
        ],
        string="Employee Evaluation Type",
        default='standard',
        tracking=True,
        required=True,
    )

    def _compute_evaluation_count(self):
        for employee in self:
            employee.evaluation_count = self.env['employee.evaluation'].search_count(
                [('employee_id', '=', employee.id)]
            )

    def action_open_evaluations(self):
        """Open evaluations for this employee (smart button action)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Evaluations - {self.name}',
            'res_model': 'employee.evaluation',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
        }

    def action_create_evaluation(self):
        """Create a new evaluation form pre-filled for this employee."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'New Evaluation - {self.name}',
            'res_model': 'employee.evaluation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_employee_id': self.id,
            },
        }


class HREmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    emp_eval_type = fields.Selection(
        [
            ('supervisor', 'Supervisor/Manager'),
            ('standard', 'Employee'),
        ],
        string="Employee Evaluation Type",
    )
