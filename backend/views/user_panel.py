from io import BytesIO
import base64

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from PIL import Image

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
        {'url': '/user/profile/', 'label': 'Profile'},
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


def _save_profile_image_from_data_url(profile_obj, data_url):
    header, encoded = data_url.split(';base64,', 1)
    ext = 'png' if 'png' in header else 'jpg'
    image_bytes = base64.b64decode(encoded)
    image = Image.open(BytesIO(image_bytes)).convert('RGB')
    image.thumbnail((512, 512))
    output = BytesIO()
    image.save(output, format='JPEG', quality=85, optimize=True)
    profile_obj.profile_image.save(f'avatar_{profile_obj.user_id}.{ext}', ContentFile(output.getvalue()), save=True)


def _profile_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile_obj = get_user_profile(request.user)
    if not profile_obj:
        return redirect('login')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_image':
            cropped = request.POST.get('cropped_image')
            if not cropped or ';base64,' not in cropped:
                messages.error(request, 'Unable to process image upload.')
                write_activity_log(action_type='Profile Image Update', module_name='Profile', description='Profile image update failed due to invalid image payload.', status=ActivityLog.STATUS_FAILED, user=request.user)
            else:
                _save_profile_image_from_data_url(profile_obj, cropped)
                messages.success(request, 'Profile image updated successfully.')
                write_activity_log(action_type='Profile Image Update', module_name='Profile', description='Profile image updated successfully.', status=ActivityLog.STATUS_SUCCESS, user=request.user)
        elif action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            if not request.user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                write_activity_log(action_type='Password Change Attempt', module_name='Profile', description='Failed password change attempt: incorrect current password.', status=ActivityLog.STATUS_FAILED, user=request.user)
            elif new_password != confirm_password:
                messages.error(request, 'New password and confirm password do not match.')
            else:
                try:
                    validate_password(new_password, request.user)
                    request.user.set_password(new_password)
                    request.user.save(update_fields=['password'])
                    update_session_auth_hash(request, request.user)
                    messages.success(request, 'Password changed successfully.')
                    write_activity_log(action_type='Password Changed', module_name='Profile', description='Password changed successfully.', status=ActivityLog.STATUS_SUCCESS, user=request.user)
                except ValidationError as exc:
                    messages.error(request, ' '.join(exc.messages))
                    write_activity_log(action_type='Password Change Attempt', module_name='Profile', description='Failed password change attempt due to password policy validation.', status=ActivityLog.STATUS_FAILED, user=request.user)

        target = 'admin_profile' if profile_obj.role == 'Admin' else 'user_profile'
        return redirect(target)

    template_name = 'admin_panel/admin_profile.html' if profile_obj.role == 'Admin' else 'user_panel/profile.html'
    sidebar_menu = [{'url': '/admin-panel/profile/', 'label': 'Profile'}] if profile_obj.role == 'Admin' else _sidebar_menu_for_role(profile_obj.role)

    return render(request, template_name, {
        'profile_obj': profile_obj,
        'sidebar_menu': sidebar_menu,
    })


def user_profile(request):
    profile_obj = get_user_profile(request.user)
    if not profile_obj or profile_obj.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile_obj)
    return _profile_view(request)


def admin_profile(request):
    profile_obj = get_user_profile(request.user)
    if not profile_obj or profile_obj.role != 'Admin':
        return redirect_for_profile(profile_obj)
    return _profile_view(request)


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
