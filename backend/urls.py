from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('my-checklists/', views.my_checklists, name='my_checklists'),
    path('my-checklists/<int:checklist_id>/view/', views.user_checklist_preview, name='user_checklist_preview'),
    path('my-checklists/<int:checklist_id>/fill/', views.user_checklist_fill, name='user_checklist_fill'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('admin-panel/profile/', views.admin_profile, name='admin_profile'),

    path('management-dashboard/', views.management_dashboard, name='management_dashboard'),

    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/departments/', views.admin_departments, name='admin_departments'),
    path('admin-panel/projects/', views.admin_projects, name='admin_projects'),
    path('admin-panel/checklists/', views.admin_checklists, name='admin_checklists'),
    path('admin-panel/checklists/create/', views.admin_checklist_create, name='admin_checklist_create'),
    path('admin-panel/checklists/<int:checklist_id>/edit/', views.admin_checklist_edit, name='admin_checklist_edit'),
    path('admin-panel/checklists/<int:checklist_id>/view/', views.admin_checklist_view, name='admin_checklist_view'),
    path('admin-panel/checklists/<int:checklist_id>/pdf/', views.admin_checklist_pdf, name='admin_checklist_pdf'),
    path('admin-panel/responses/', views.admin_responses, name='admin_responses'),
    path('admin-panel/logs/', views.admin_logs, name='admin_logs'),

    path('admin-create/', views.admin_master_create, name='admin_master_create'),
    path('admin-master-create/', views.admin_master_create_legacy, name='admin_create'),
    path('admin-user-action/', views.admin_user_action, name='admin_user_action'),
    path('admin-department-action/', views.admin_department_action, name='admin_department_action'),
    path('admin-project-action/', views.admin_project_action, name='admin_project_action'),
    path('admin-checklist-action/', views.admin_checklist_action, name='admin_checklist_action'),
    path('admin-response-action/', views.admin_response_action, name='admin_response_action'),
]
