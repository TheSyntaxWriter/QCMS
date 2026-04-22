from .admin import (
    admin_checklists,
    admin_dashboard,
    admin_departments,
    admin_master_create,
    admin_master_create_legacy,
    admin_department_action,
    admin_checklist_action,
    admin_project_action,
    admin_projects,
    admin_response_action,
    admin_responses,
    admin_user_action,
    admin_users,
)
from .auth import home, user_login, user_logout
from .checklist import checklist_detail, view_checklist
from .hod import hod_dashboard, update_status
from .management import management_dashboard
from .user_panel import dashboard, my_checklists, my_submissions

__all__ = [
    'home',
    'user_login',
    'user_logout',
    'checklist_detail',
    'view_checklist',
    'hod_dashboard',
    'update_status',
    'admin_dashboard',
    'admin_users',
    'admin_departments',
    'admin_projects',
    'admin_checklists',
    'admin_responses',
    'admin_master_create',
    'admin_master_create_legacy',
    'admin_department_action',
    'admin_checklist_action',
    'admin_project_action',
    'admin_user_action',
    'admin_response_action',
    'management_dashboard',
    'my_checklists',
    'my_submissions',
    'dashboard',
]
