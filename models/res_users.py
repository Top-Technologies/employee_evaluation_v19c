from odoo import models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_evaluation_admin_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'group_ids' in vals and not self.env.context.get('syncing_evaluation_group'):
            self.with_context(syncing_evaluation_group=True)._sync_evaluation_admin_group()
        return res

    def _sync_evaluation_admin_group(self):
        eval_hr = self.env.ref('employee_evaluation_v19c.group_evaluation_hr', raise_if_not_found=False)
        sys_admin = self.env.ref('base.group_system', raise_if_not_found=False)
        hr_admin = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)

        if not (eval_hr and sys_admin and hr_admin):
            return

        for user in self:
            # User must have BOTH Administrator role AND Employee Admin access
            has_sys_admin = user.has_group('base.group_system')
            has_hr_admin = user.has_group('hr.group_hr_manager')
            if has_sys_admin and has_hr_admin:
                if eval_hr not in user.group_ids:
                    user.with_context(syncing_evaluation_group=True).write({'group_ids': [(4, eval_hr.id)]})
            else:
                if eval_hr in user.group_ids:
                    user.with_context(syncing_evaluation_group=True).write({'group_ids': [(3, eval_hr.id)]})

    @api.model
    def _register_hook(self):
        super()._register_hook()
        # Automatically sync evaluation group on all non-share users when registry is ready
        self.search([('share', '=', False)]).with_context(syncing_evaluation_group=True)._sync_evaluation_admin_group()

