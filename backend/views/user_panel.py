from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404

from ..models import ChecklistDefinition, ChecklistResponse, RolePermission
from .common import get_user_profile, redirect_for_profile
from .admin import _checklist_preview_context
from ..logging_service import write_activity_log
from ..models import ActivityLog

DEFAULT_VISIBLE_COLUMNS = [
    'checklist_id', 'checklist_name', 'checklist_type', 'submitted_by',
    'project', 'department', 'hod_name', 'submission_datetime', 'status',
    'last_updated_by', 'last_updated', 'actions',
]
DEFAULT_ALLOWED_ACTIONS = ['view', 'edit', 'approve', 'reject', 'delete', 'toggle']


def _sidebar_menu_for_role(role):
    items = [
        {'url': '/my-checklists/', 'label': 'My Checklists'},
        {'url': '/my-submissions/', 'label': 'My Submissions'},
        {'url': '/profile/', 'label': 'Profile'},
    ]
    if role == 'Management':
        items.insert(0, {'url': '/dashboard/', 'label': 'Dashboard'})
    return items


def _checklists_for_profile(profile):
    qs = ChecklistDefinition.objects.select_related('checklist_type').prefetch_related('projects', 'departments')
    if profile.role == 'Management':
        return qs
    if profile.role == 'HOD':
        return qs.filter(departments=profile.department)
    user_project = profile.project
    user_domain = profile.project.domain if profile.project else None
    return qs.filter(departments=profile.department).filter(
        Q(projects=user_project) | Q(projects__domain=user_domain),
    ).distinct()


def _responses_for_profile(profile, user):
    qs = ChecklistResponse.objects.select_related(
        'checklist', 'submitted_by', 'project', 'department', 'hod', 'updated_by', 'checklist__checklist_type',
    )
    if profile.role == 'Management':
        return qs
    if profile.role == 'HOD':
        return qs.filter(department=profile.department)
    return qs.filter(submitted_by=user)


def _permission_for_role(role):
    permission = RolePermission.objects.filter(role=role).first()
    if not permission:
        return DEFAULT_VISIBLE_COLUMNS, DEFAULT_ALLOWED_ACTIONS
    visible_columns = permission.visible_columns or DEFAULT_VISIBLE_COLUMNS
    allowed_actions = permission.allowed_actions or DEFAULT_ALLOWED_ACTIONS
    return visible_columns, allowed_actions


def my_checklists(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    checklists = Paginator(_checklists_for_profile(profile).order_by('-updated_at'), 8).get_page(request.GET.get('page'))

    return render(request, 'user_panel/my_checklists.html', {
        'checklists': checklists,
        'sidebar_menu': _sidebar_menu_for_role(profile.role),
    })


def my_submissions(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    visible_columns, allowed_actions = _permission_for_role(profile.role)
    responses = Paginator(_responses_for_profile(profile, request.user).order_by('-submitted_at'), 10).get_page(request.GET.get('page'))

    return render(request, 'user_panel/my_submissions.html', {
        'responses': responses,
        'visible_columns': visible_columns,
        'allowed_actions': allowed_actions,
        'sidebar_menu': _sidebar_menu_for_role(profile.role),
    })


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != 'Management':
        return redirect_for_profile(profile)

    return render(request, 'user_panel/dashboard.html', {
        'sidebar_menu': _sidebar_menu_for_role(profile.role),
    })


def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile_obj = get_user_profile(request.user)
    if not profile_obj:
        return redirect('login')

    return render(request, 'user_panel/profile.html', {
        'profile_obj': profile_obj,
        'sidebar_menu': _sidebar_menu_for_role(profile_obj.role),
    })


def user_checklist_preview(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    item = get_object_or_404(
        _checklists_for_profile(profile).prefetch_related('questions', 'projects', 'departments'),
        id=checklist_id,
    )
    write_activity_log(action_type='Checklist Viewed', module_name='Checklist', description=f'Checklist preview viewed: {item.checklist_id}', status=ActivityLog.STATUS_INFO, user=request.user)
    if request.GET.get('print') == '1':
        write_activity_log(action_type='Checklist Printed', module_name='Checklist', description=f'Checklist print preview opened: {item.checklist_id}', status=ActivityLog.STATUS_INFO, user=request.user)
    ctx = _checklist_preview_context(request, item)
    ctx['preview_mode'] = 'user'
    return render(request, 'admin_panel/checklist_view.html', ctx)
