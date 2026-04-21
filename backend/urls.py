from django.urls import path
from . import views

urlpatterns = [

    # =====================================================
    # 🏠 HOME / ENTRY POINT
    # =====================================================
    path('', views.home, name='home'),

    # =====================================================
    # 🔐 AUTHENTICATION
    # =====================================================
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # =====================================================
    # 📋 CHECKLIST MODULE
    # =====================================================
    path('checklist/<int:checklist_id>/', views.checklist_detail, name='checklist_detail'),

    # =====================================================
    # 🧑‍💼 HOD MODULE
    # =====================================================
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('update-status/<int:txn_id>/<str:action>/', views.update_status, name='update_status'),

    # =====================================================
    # 🔍 VIEW + HISTORY
    # =====================================================
    path('view/<int:txn_id>/', views.view_checklist, name='view_checklist'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),

    # =====================================================
    # 📊 ADMIN PANEL
    # =====================================================
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # =====================================================
    # 👤 USERS
    # =====================================================
    path('admin-panel/users/', views.admin_users, name='admin_users'),

    # =====================================================
    # 🏢 DEPARTMENTS
    # =====================================================
    path('admin-panel/departments/', views.admin_departments, name='admin_departments'),

    # =====================================================
    # 📄 RESPONSES
    # =====================================================
    path('admin-panel/responses/', views.admin_responses, name='admin_responses'),

    # =====================================================
    # 📁 PROJECTS
    # =====================================================
    path('admin-panel/projects/', views.admin_projects, name='admin_projects'),

    # =====================================================
    # 📋 CHECKLISTS
    # =====================================================
    path('admin-panel/checklists/', views.admin_checklists, name='admin_checklists'),

    # =====================================================
    # 📊 MANAGEMENT
    # =====================================================
    path('management/', views.management_dashboard, name='management_dashboard'),

    # =====================================================
    # 🔥 UNIVERSAL CREATE
    # =====================================================
    path('admin-create/', views.admin_master_create, name='admin_master_create'),

    # =====================================================
    # 🔥 USER ACTIONS (VIEW / EDIT / TOGGLE)
    # =====================================================
    path('admin-master-create/', views.admin_master_create_legacy, name='admin_create'),
    path('admin-user-action/', views.admin_user_action, name='admin_user_action'),
]
