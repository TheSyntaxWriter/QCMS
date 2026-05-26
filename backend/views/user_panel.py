from io import BytesIO
import base64

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from PIL import Image

from ..models import ChecklistDefinition, ChecklistQuestion, ChecklistResponse, ChecklistAnswer, UserProfile
from .common import get_user_profile, redirect_for_profile
from .admin import _admin_sidebar_menu, _checklist_preview_context, _checklist_pdf_filename, _render_checklist_pdf_response
from ..logging_service import write_activity_log
from ..models import ActivityLog
from ..permission_service import get_role_permission_config, responses_for_profile



def _resolve_hod_user(department):
    if not department:
        return None
    return UserProfile.objects.select_related('user').filter(
        role='HOD',
        is_active=True,
        department=department,
        user__is_active=True,
    ).order_by('id').values_list('user_id', flat=True).first()

def _sidebar_menu_for_role(role):
    items = [
        {'url': '/my-checklists/', 'label': 'Checklist', 'icon': 'checklist'},
        {'url': '/my-submissions/', 'label': 'Response', 'icon': 'response'},
        {'url': '/user/profile/', 'label': 'Profile', 'icon': 'profile'},
    ]
    if role == 'Management':
        items.insert(0, {'url': '/dashboard/', 'label': 'Dashboard', 'icon': 'dashboard'})
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

    visible_columns, allowed_actions = get_role_permission_config(profile.role)
    responses = Paginator(responses_for_profile(profile, request.user).order_by('-submitted_at'), 10).get_page(request.GET.get('page'))

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
        return redirect('home')

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
    sidebar_menu = _admin_sidebar_menu() if profile_obj.role == 'Admin' else _sidebar_menu_for_role(profile_obj.role)

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




def _extract_answer(request, question):
    key = f'q_{question.id}'
    if question.type == ChecklistQuestion.TYPE_CHECKBOX:
        values = request.POST.getlist(key)
        return ' | '.join(v for v in values if v.strip())
    if question.type == ChecklistQuestion.TYPE_FILE_UPLOAD:
        uploaded = request.FILES.get(key)
        return uploaded
    return (request.POST.get(key, '') or '').strip()


def _validate_required_questions(request, questions):
    errors = []
    for question in questions:
        if not question.required:
            continue
        value = _extract_answer(request, question)
        if question.type == ChecklistQuestion.TYPE_FILE_UPLOAD:
            if not value:
                errors.append(f'Question {question.order}: file upload is required.')
        elif not value:
            errors.append(f'Question {question.order}: answer is required.')
    return errors


def user_checklist_fill(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    checklist = get_object_or_404(
        _checklists_for_profile(profile).prefetch_related('questions', 'projects', 'departments'),
        id=checklist_id,
    )

    questions = list(checklist.questions.all().order_by('order', 'id'))

    if request.method == 'POST':
        validation_errors = _validate_required_questions(request, questions)
        if validation_errors:
            for err in validation_errors:
                messages.error(request, err)
        else:
            with transaction.atomic():
                hod_user_id = _resolve_hod_user(profile.department)
                response = ChecklistResponse.objects.create(
                    checklist=checklist,
                    submitted_by=request.user,
                    project=profile.project,
                    department=profile.department,
                    hod_id=hod_user_id,
                    status='Pending',
                    updated_by=request.user,
                )
                for question in questions:
                    value = _extract_answer(request, question)
                    answer = ChecklistAnswer(response=response, question=question)
                    if question.type == ChecklistQuestion.TYPE_FILE_UPLOAD:
                        if value:
                            answer.file = value
                    else:
                        answer.answer_text = value
                    answer.save()

            write_activity_log(action_type='Checklist Submitted', module_name='Checklist', description=f'Checklist submitted: {checklist.checklist_id} by {request.user.username}', status=ActivityLog.STATUS_SUCCESS, user=request.user)
            messages.success(request, f'Checklist {checklist.checklist_id} submitted successfully.')
            return redirect('my_submissions')

    sectioned = {}
    for question in questions:
        sectioned.setdefault(question.section or 'General', []).append(question)

    return render(request, 'user_panel/checklist_fill.html', {
        'checklist': checklist,
        'sectioned_questions': list(sectioned.items()),
        'sidebar_menu': _sidebar_menu_for_role(profile.role),
    })



def user_submission_action(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    if request.method == 'POST':
        action = request.POST.get('action')
        response_id = request.POST.get('response_id')
        allowed_actions = set(get_role_permission_config(profile.role)[1])
        if action not in allowed_actions:
            return JsonResponse({'ok': False, 'error': 'Unauthorized action'}, status=403)
        response = responses_for_profile(profile, request.user).filter(id=response_id).first()
        if not response:
            return JsonResponse({'ok': False, 'error': 'Response not found'}, status=404)
        if action in {'approve', 'reject'}:
            response.status = 'Approved' if action == 'approve' else 'Rejected'
            response.updated_by = request.user
            response.save(update_fields=['status', 'updated_by', 'updated_at'])
            return JsonResponse({'ok': True, 'status': response.status})
        return JsonResponse({'ok': False, 'error': 'Invalid action'}, status=400)

    action = request.GET.get('action')
    response_id = request.GET.get('response_id')
    if action != 'view' or not response_id:
        return JsonResponse({'ok': False}, status=400)

    response = responses_for_profile(profile, request.user).select_related(
        'checklist', 'project', 'department', 'submitted_by',
    ).prefetch_related('answers__question').filter(id=response_id).first()
    if not response:
        return JsonResponse({'ok': False}, status=404)

    return JsonResponse({
        'ok': True,
        'checklist_id': response.checklist.checklist_id,
        'checklist_name': response.checklist.name,
        'submitted_by': response.submitted_by.username if response.submitted_by else '',
        'answers': [{
            'question': answer.question.question_text,
            'answer_text': answer.answer_text,
            'file_url': answer.file.url if answer.file else '',
        } for answer in response.answers.all()],
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
    ctx['sidebar_menu'] = _sidebar_menu_for_role(profile.role)
    return render(request, 'user_panel/checklist_view.html', ctx)


def user_checklist_pdf(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role not in {'User', 'HOD', 'Management'}:
        return redirect_for_profile(profile)

    item = get_object_or_404(
        _checklists_for_profile(profile).prefetch_related('questions', 'projects', 'departments'),
        id=checklist_id,
    )
    write_activity_log(action_type='Checklist PDF Downloaded', module_name='Checklist', description=f'Checklist PDF downloaded: {item.checklist_id}', status=ActivityLog.STATUS_SUCCESS, user=request.user)

    context = _checklist_preview_context(request, item, pdf_mode=False)
    context['preview_mode'] = 'user'
    context['sidebar_menu'] = _sidebar_menu_for_role(profile.role)
    filename = _checklist_pdf_filename(item)
    return _render_checklist_pdf_response(request, context, filename, 'user_panel/checklist_view.html')
