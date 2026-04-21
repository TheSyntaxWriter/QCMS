from .admin import (
    admin_checklists,
    admin_dashboard,
    admin_departments,
    admin_master_create,
    admin_master_create_legacy,
    admin_projects,
    admin_responses,
    admin_user_action,
    admin_users,
)
from .auth import home, user_login, user_logout
from .checklist import checklist_detail, my_submissions, view_checklist
from .hod import hod_dashboard, update_status
from .management import management_dashboard

__all__ = [
    'home',
    'user_login',
    'user_logout',
    'checklist_detail',
    'view_checklist',
    'my_submissions',
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
    'admin_user_action',
    'management_dashboard',
]
