from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('my-checklists/', views.my_checklists, name='my_checklists'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),

    path('checklist/<int:checklist_id>/', views.checklist_detail, name='checklist_detail'),
    path('submission/<int:txn_id>/', views.view_checklist, name='view_checklist'),
    path('submission/<int:txn_id>/update-status/', views.update_status, name='update_status'),
    path('management-dashboard/', views.management_dashboard, name='management_dashboard'),

    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/departments/', views.admin_departments, name='admin_departments'),
    path('admin-panel/projects/', views.admin_projects, name='admin_projects'),
    path('admin-panel/checklists/', views.admin_checklists, name='admin_checklists'),
    path('admin-panel/responses/', views.admin_responses, name='admin_responses'),

    path('admin-create/', views.admin_master_create, name='admin_master_create'),
    path('admin-master-create/', views.admin_master_create_legacy, name='admin_create'),
    path('admin-user-action/', views.admin_user_action, name='admin_user_action'),
    path('admin-department-action/', views.admin_department_action, name='admin_department_action'),
    path('admin-project-action/', views.admin_project_action, name='admin_project_action'),
    path('admin-checklist-action/', views.admin_checklist_action, name='admin_checklist_action'),
    path('admin-response-action/', views.admin_response_action, name='admin_response_action'),
]
