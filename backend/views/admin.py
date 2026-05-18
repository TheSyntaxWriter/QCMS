import re
from pathlib import Path
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.contrib.staticfiles import finders
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from ..models import (
    ChecklistAnswer,
    ChecklistDefinition,
    ChecklistQuestion,
    ChecklistResponse,
    ChecklistType,
    Department,
    Project,
    RolePermission,
    UserProfile,
)
from .common import get_user_profile






def _admin_sidebar_menu():
    return [
        {'url': '/admin-panel/', 'label': 'Dashboard'},
        {'url': '/admin-panel/users/', 'label': 'Users'},
        {'url': '/admin-panel/departments/', 'label': 'Departments'},
        {'url': '/admin-panel/projects/', 'label': 'Projects'},
        {'url': '/admin-panel/checklists/', 'label': 'Checklists'},
        {'url': '/admin-panel/responses/', 'label': 'Responses'},
    ]
def _clean_email_or_error(request, raw_email):
    email = (raw_email or '').strip()
    if not email:
        messages.error(request, "Email is required.")
        return None

    try:
        validate_email(email)
    except ValidationError:
        messages.error(request, "Please enter a valid email address.")
        return None

    return email


def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    # Keep a base queryset so summary cards and table stay consistent.
    txns = ChecklistResponse.objects.select_related('checklist', 'submitted_by').order_by('-submitted_at')

    # ---------------------------
    # Card totals + pie datasets
    # ---------------------------
    total_users = UserProfile.objects.count()
    total_checklists = ChecklistDefinition.objects.count()
    total_departments = Department.objects.count()
    total_projects = Project.objects.count()
    total_submitted = txns.count()

    users_active = UserProfile.objects.filter(is_active=True).count()
    users_inactive = UserProfile.objects.filter(is_active=False).count()

    checklists_active = ChecklistDefinition.objects.filter(is_active=True).count()
    checklists_inactive = ChecklistDefinition.objects.filter(is_active=False).count()

    approved = txns.filter(status='Approved').count()
    pending = txns.filter(status='Pending').count()
    rejected = txns.filter(status='Rejected').count()

    # ---------------------------------------------
    # Column chart datasets (users by master entity)
    # ---------------------------------------------
    department_stats = (
        Department.objects
        .annotate(
            active_users=Count('userprofile', filter=Q(userprofile__is_active=True)),
            inactive_users=Count('userprofile', filter=Q(userprofile__is_active=False)),
        )
        .order_by('name')
    )

    project_stats = (
        Project.objects
        .annotate(
            active_users=Count('userprofile', filter=Q(userprofile__is_active=True)),
            inactive_users=Count('userprofile', filter=Q(userprofile__is_active=False)),
        )
        .order_by('name')
    )

    dashboard_config = {
        'totals': {
            'users': total_users,
            'checklists': total_checklists,
            'departments': total_departments,
            'projects': total_projects,
            'submittedChecklists': total_submitted,
        },
        'charts': {
            # Pie chart data for user activation split.
            'users': {
                'active': users_active,
                'inactive': users_inactive,
            },
            # Pie chart data for checklist activation split.
            'checklists': {
                'active': checklists_active,
                'inactive': checklists_inactive,
            },
            # Column chart data for active/inactive users in each department.
            'departments': {
                'labels': [department.name for department in department_stats],
                'activeUsers': [department.active_users for department in department_stats],
                'inactiveUsers': [department.inactive_users for department in department_stats],
            },
            # Column chart data for active/inactive users in each project.
            'projects': {
                'labels': [f'{project.name} ({project.domain})' for project in project_stats],
                'activeUsers': [project.active_users for project in project_stats],
                'inactiveUsers': [project.inactive_users for project in project_stats],
            },
            # Pie chart data for checklist submission status split.
            'submittedChecklists': {
                'approved': approved,
                'pending': pending,
                'rejected': rejected,
            },
        },
    }

    return render(request, 'admin_panel/admin_dashboard.html', {
        'sidebar_menu': _admin_sidebar_menu(),
        'transactions': txns[:8],
        'total_users': total_users,
        'total_checklists': total_checklists,
        'total_departments': total_departments,
        'total_projects': total_projects,
        'total_submitted_checklists': total_submitted,
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'admin_dashboard_config': dashboard_config,
    })


def admin_users(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    search_query = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')
    proj_filter = request.GET.get('project', '')
    stat_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'username')
    sort_dir = request.GET.get('dir', 'asc')

    user_list = UserProfile.objects.select_related('user', 'department', 'project')

    if search_query:
        user_list = user_list.filter(
            Q(user__username__icontains=search_query)
            | Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
        )
    if dept_filter:
        user_list = user_list.filter(department_id=dept_filter)
    if proj_filter:
        user_list = user_list.filter(project_id=proj_filter)
    if stat_filter:
        is_active = stat_filter == 'active'
        user_list = user_list.filter(is_active=is_active)

    allowed_sort_fields = {
        'username': 'user__username',
        'full_name': 'user__first_name',
        'role': 'role',
        'department': 'department__name',
        'project': 'project__name',
        'status': 'is_active',
    }
    if sort_by not in allowed_sort_fields:
        sort_by = 'username'
    if sort_dir not in {'asc', 'desc'}:
        sort_dir = 'asc'

    order_field = allowed_sort_fields[sort_by]
    if sort_dir == 'desc':
        order_field = f'-{order_field}'
    user_list = user_list.order_by(order_field, 'user__username')

    base_params = {
        'search': search_query,
        'department': dept_filter,
        'project': proj_filter,
        'status': stat_filter,
    }

    sort_links = {}
    for key in allowed_sort_fields:
        next_dir = 'desc' if sort_by == key and sort_dir == 'asc' else 'asc'
        params = {**base_params, 'sort': key, 'dir': next_dir}
        sort_links[key] = urlencode({k: v for k, v in params.items() if v != ''})

    filtered_user_list = user_list

    role_counts = {
        'user': filtered_user_list.filter(role='User').count(),
        'hod': filtered_user_list.filter(role='HOD').count(),
        'management': filtered_user_list.filter(role='Management').count(),
    }

    total_active = filtered_user_list.filter(is_active=True).count()
    total_inactive = filtered_user_list.filter(is_active=False).count()

    dept_stats = (
        filtered_user_list
        .values('department__name')
        .annotate(
            active_count=Count('id', filter=Q(is_active=True)),
            inactive_count=Count('id', filter=Q(is_active=False)),
        )
        .order_by('department__name')
    )

    dept_labels = [department['department__name'] or "Unassigned" for department in dept_stats]
    dept_active_data = [department['active_count'] for department in dept_stats]
    dept_inactive_data = [department['inactive_count'] for department in dept_stats]

    paginator = Paginator(filtered_user_list, 10)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)

    context = {
        'sidebar_menu': _admin_sidebar_menu(),
        'users': users_page,
        'departments': Department.objects.all(),
        'projects': Project.objects.all(),
        'role_counts': role_counts,
        'active_users': total_active,
        'inactive_users': total_inactive,
        'dept_labels': dept_labels,
        'dept_active_data': dept_active_data,
        'dept_inactive_data': dept_inactive_data,
        'sort_by': sort_by,
        'sort_dir': sort_dir,
        'sort_links': sort_links,
        'pagination_query': urlencode({k: v for k, v in {
            'search': search_query,
            'department': dept_filter,
            'project': proj_filter,
            'status': stat_filter,
            'sort': sort_by,
            'dir': sort_dir,
        }.items() if v != ''}),
        'users_page': users_page,
        'admin_users_config': {
            'createUrl': '/admin-create/',
            'editUrl': '/admin-user-action/',
            'csrfToken': get_token(request),
            'departments': [
                {'id': d.id, 'name': d.name} for d in Department.objects.all()
            ],
            'projects': [
                {'id': p.id, 'name': p.name, 'domain': p.domain} for p in Project.objects.all()
            ],
            'charts': {
                'active': total_active,
                'inactive': total_inactive,
                'deptLabels': dept_labels,
                'deptActiveData': dept_active_data,
                'deptInactiveData': dept_inactive_data,
            },
        },
    }

    return render(request, 'admin_panel/admin_users.html', context)


def admin_departments(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    departments = Department.objects.all().order_by('id')
    return render(request, 'admin_panel/admin_departments.html', {
        'sidebar_menu': _admin_sidebar_menu(),
        'departments': departments,
        'admin_departments_config': {
            'createUrl': '/admin-create/',
            'actionUrl': '/admin-department-action/',
            'csrfToken': get_token(request),
        },
    })


def admin_projects(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    projects = Project.objects.all().order_by('id')
    return render(request, 'admin_panel/admin_projects.html', {
        'sidebar_menu': _admin_sidebar_menu(),
        'projects': projects,
        'admin_projects_config': {
            'createUrl': '/admin-create/',
            'actionUrl': '/admin-project-action/',
            'csrfToken': get_token(request),
        },
    })


def admin_checklists(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    search = (request.GET.get('search') or '').strip()
    checklist_type = (request.GET.get('checklist_type') or '').strip()
    status = (request.GET.get('status') or '').strip()
    page_no = request.GET.get('page')

    checklists = ChecklistDefinition.objects.select_related('checklist_type').prefetch_related('projects', 'departments')

    if search:
        checklists = checklists.filter(Q(checklist_id__icontains=search) | Q(name__icontains=search))
    if checklist_type:
        checklists = checklists.filter(checklist_type_id=checklist_type)
    if status in {'active', 'inactive'}:
        checklists = checklists.filter(is_active=(status == 'active'))

    paginator = Paginator(checklists.order_by('-updated_at'), 8)
    page_obj = paginator.get_page(page_no)

    if request.GET.get('ajax') == '1':
        rows = []
        for item in page_obj:
            rows.append({
                'id': item.id,
                'checklist_id': item.checklist_id,
                'name': item.name,
                'checklist_type': item.checklist_type.name,
                'departments': [department.name for department in item.departments.all()],
                'updated_at': item.updated_at.strftime('%d-%m-%Y %H:%M'),
                'status': 'Active' if item.is_active else 'Inactive',
            })
        return JsonResponse({
            'rows': rows,
            'pagination': {
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'number': page_obj.number,
                'num_pages': paginator.num_pages,
            },
        })

    return render(request, 'admin_panel/admin_checklists.html', {
        'sidebar_menu': _admin_sidebar_menu(),
        'checklists': page_obj,
        'checklist_types': ChecklistType.objects.filter(is_active=True).order_by('name'),
        'projects': Project.objects.filter(is_active=True).order_by('name'),
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'questions_json_help': {
            'types': _question_type_options(),
        },
    })


def _question_type_options():
    return [
        {'value': value, 'label': label}
        for value, label in ChecklistQuestion.QUESTION_TYPES
    ]


def _question_type_label_map():
    return dict(ChecklistQuestion.QUESTION_TYPES)





def _checklist_pdf_filename(item):
    base = re.sub(r'[^A-Za-z0-9_-]+', '_', item.name or 'Checklist').strip('_') or 'Checklist'
    return f'{base}.pdf'


def _static_file_uri(static_path):
    resolved = finders.find(static_path)
    if not resolved:
        return ''
    return Path(resolved).resolve().as_uri()

def _checklist_preview_context(request, item, pdf_mode=False):
    type_labels = _question_type_label_map()
    sections_by_title = {}
    for question in item.questions.all().order_by('order', 'id'):
        section_title = (question.section or '').strip() or 'Section 1'
        section = sections_by_title.setdefault(section_title, {
            'title': section_title,
            'questions': [],
        })
        section['questions'].append({
            'text': question.question_text,
            'type': question.type,
            'type_label': type_labels.get(question.type, question.type),
            'options': question.options or [],
            'required': question.required,
            'order': question.order,
        })

    return {
        'sidebar_menu': [] if pdf_mode else _admin_sidebar_menu(),
        'checklist': item,
        'sections': list(sections_by_title.values()),
        'pdf_mode': pdf_mode,
        'auto_print': request.GET.get('print') == '1',
        'logo_url': _static_file_uri('images/logo.png') if pdf_mode else '',
    }


def _checklist_builder_context(request, item=None):
    latest = ChecklistDefinition.objects.filter(checklist_id__iregex=r'^CL[0-9]+$').order_by('-id')
    max_num = 0
    for row in latest:
        digits = ''.join(ch for ch in (row.checklist_id or '') if ch.isdigit())
        if digits:
            max_num = max(max_num, int(digits))
    next_checklist_id = f"CL{str(max_num + 1).zfill(2)}"

    sections_by_title = {}
    if item:
        for q in item.questions.all().order_by('order', 'id'):
            section_title = (q.section or '').strip() or 'Section 1'
            section = sections_by_title.setdefault(section_title, {
                'id': f'section_{len(sections_by_title) + 1}',
                'title': section_title,
                'order': len(sections_by_title) + 1,
                'collapsed': False,
                'questions': [],
            })
            section['questions'].append({
                'id': q.id,
                'text': q.question_text,
                'type': q.type,
                'options': q.options or [],
                'required': q.required,
                'order': len(section['questions']) + 1,
            })

    initial_sections = list(sections_by_title.values())

    return {
        'sidebar_menu': _admin_sidebar_menu(),
        'builder_mode': 'edit' if item else 'create',
        'builder_item': item,
        'next_checklist_id': item.checklist_id if item else next_checklist_id,
        'checklist_types': ChecklistType.objects.filter(is_active=True).order_by('name'),
        'projects': Project.objects.filter(is_active=True).order_by('name'),
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'questions_json_help': {
            'types': _question_type_options(),
        },
        'initial_builder_data': {'sections': initial_sections},
    }


def admin_checklist_create(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')
    return render(request, 'admin_panel/checklist_create.html', _checklist_builder_context(request))


def admin_checklist_edit(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')
    item = get_object_or_404(
        ChecklistDefinition.objects.select_related('checklist_type').prefetch_related('projects', 'departments', 'questions'),
        id=checklist_id,
    )
    return render(request, 'admin_panel/checklist_create.html', _checklist_builder_context(request, item=item))


def admin_checklist_view(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')
    item = get_object_or_404(
        ChecklistDefinition.objects.select_related('checklist_type').prefetch_related('projects', 'departments', 'questions'),
        id=checklist_id,
    )
    return render(request, 'admin_panel/checklist_view.html', _checklist_preview_context(request, item))


def admin_checklist_pdf(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')
    item = get_object_or_404(
        ChecklistDefinition.objects.select_related('checklist_type').prefetch_related('projects', 'departments', 'questions'),
        id=checklist_id,
    )

    # IMPORTANT: render the same DOM/CSS state as checklist preview so browser print preview
    # and downloaded PDF stay visually consistent.
    context = _checklist_preview_context(request, item, pdf_mode=False)
    filename = _checklist_pdf_filename(item)

    from weasyprint import HTML

    html = render_to_string('admin_panel/checklist_view.html', context, request=request)
    pdf_bytes = HTML(
        string=html,
        base_url=request.build_absolute_uri('/'),
    ).write_pdf(media_type='print', presentational_hints=True, optimize_size=('fonts', 'images'))

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def admin_responses(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    project_filter = (request.GET.get('project') or '').strip()
    department_filter = (request.GET.get('department') or '').strip()
    status_filter = (request.GET.get('status') or '').strip()
    search = (request.GET.get('search') or '').strip()
    date_from = (request.GET.get('date_from') or '').strip()
    date_to = (request.GET.get('date_to') or '').strip()

    responses = ChecklistResponse.objects.select_related(
        'checklist', 'submitted_by', 'project', 'department', 'hod', 'updated_by', 'checklist__checklist_type',
    )
    if project_filter:
        responses = responses.filter(project_id=project_filter)
    if department_filter:
        responses = responses.filter(department_id=department_filter)
    if status_filter:
        responses = responses.filter(status=status_filter)
    if date_from:
        responses = responses.filter(submitted_at__date__gte=date_from)
    if date_to:
        responses = responses.filter(submitted_at__date__lte=date_to)
    if search:
        responses = responses.filter(
            Q(checklist__checklist_id__icontains=search)
            | Q(checklist__name__icontains=search)
            | Q(submitted_by__username__icontains=search)
        )

    stats = responses.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='Pending')),
        approved=Count('id', filter=Q(status='Approved')),
        rejected=Count('id', filter=Q(status='Rejected')),
    )

    project_chart = list(
        responses.values('project__name', 'project__domain')
        .annotate(total=Count('id'))
        .order_by('project__name')
    )
    department_chart = list(
        responses.values('department__name')
        .annotate(total=Count('id'))
        .order_by('department__name')
    )
    line_chart = list(
        responses.annotate(day=TruncDate('submitted_at'))
        .values('day')
        .annotate(total=Count('id'))
        .order_by('day')
    )

    page_obj = Paginator(responses.order_by('-submitted_at'), 10).get_page(request.GET.get('page'))

    active_projects = Project.objects.filter(is_active=True).order_by('name')

    role_permissions = {
        permission.role: {
            'visible_columns': permission.visible_columns,
            'selected_projects': permission.selected_projects,
            'allowed_actions': permission.allowed_actions,
        } for permission in RolePermission.objects.all()
    }

    return render(request, 'admin_panel/admin_responses.html', {
        'sidebar_menu': _admin_sidebar_menu(),
        'visible_columns': ['checklist_id','checklist_name','checklist_type','submitted_by','project','department','hod_name','submission_datetime','status','last_updated_by','last_updated','actions'],
        'allowed_actions': ['view','edit','approve','reject','delete','toggle'],
        'responses': page_obj,
        'projects': active_projects,
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'stats': stats,
        'role_permissions': role_permissions,
        'chart_data': {
            'project_labels': [f"{row['project__name']} ({row['project__domain']})" for row in project_chart],
            'project_values': [row['total'] for row in project_chart],
            'department_labels': [row['department__name'] or 'N/A' for row in department_chart],
            'department_values': [row['total'] for row in department_chart],
            'day_labels': [row['day'].strftime('%d-%m-%Y') for row in line_chart if row['day']],
            'day_values': [row['total'] for row in line_chart if row['day']],
        },
    })


def admin_checklist_action(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')
    if request.method != 'POST':
        return redirect('admin_checklists')

    action = request.POST.get('action')
    checklist_id = request.POST.get('checklist_pk')
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if action == 'delete' and checklist_id:
        ChecklistDefinition.objects.filter(id=checklist_id).delete()
        if is_ajax:
            return JsonResponse({'ok': True})
        return redirect('admin_checklists')
    if action == 'toggle' and checklist_id:
        item = ChecklistDefinition.objects.filter(id=checklist_id).first()
        if item:
            item.is_active = not item.is_active
            item.save(update_fields=['is_active', 'updated_at'])
        if is_ajax:
            return JsonResponse({'ok': True, 'is_active': item.is_active if item else None})
        return redirect('admin_checklists')

    if action in {'create', 'edit'}:
        import json

        raw_payload = request.POST.get('builder_state_json') or '{"sections": []}'
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            return JsonResponse({'ok': False, 'errors': ['Builder data is invalid. Please refresh and try again.']}, status=400)

        sections_payload = payload.get('sections') or []
        allowed_types = {value for value, _label in ChecklistQuestion.QUESTION_TYPES}
        option_types = {
            ChecklistQuestion.TYPE_MULTIPLE_CHOICE,
            ChecklistQuestion.TYPE_CHECKBOX,
            ChecklistQuestion.TYPE_DROPDOWN,
        }
        errors = []

        checklist_code = (request.POST.get('checklist_id') or '').strip().upper()
        name = (request.POST.get('name') or '').strip()
        checklist_type_id = (request.POST.get('checklist_type') or '').strip()
        project_ids = [value for value in request.POST.getlist('projects') if str(value).isdigit()]
        department_ids = [value for value in request.POST.getlist('departments') if str(value).isdigit()]

        item = None
        if action == 'edit':
            item = ChecklistDefinition.objects.filter(id=checklist_id).first()
            if not item:
                errors.append('Checklist was not found or has already been deleted.')

        if not checklist_code:
            errors.append('Checklist ID is required.')
        elif ChecklistDefinition.objects.filter(checklist_id__iexact=checklist_code).exclude(id=item.id if item else None).exists():
            errors.append('Checklist ID already exists.')

        if not name:
            errors.append('Checklist name is required.')

        checklist_type = None
        if not checklist_type_id:
            errors.append('Checklist type is required.')
        else:
            checklist_type = ChecklistType.objects.filter(id=checklist_type_id, is_active=True).first()
            if not checklist_type:
                errors.append('Selected checklist type is invalid or inactive.')

        if project_ids:
            found_project_count = Project.objects.filter(id__in=project_ids, is_active=True).count()
            if found_project_count != len(set(project_ids)):
                errors.append('One or more selected projects are invalid or inactive.')
        if department_ids:
            found_department_count = Department.objects.filter(id__in=department_ids, is_active=True).count()
            if found_department_count != len(set(department_ids)):
                errors.append('One or more selected departments are invalid or inactive.')

        if not sections_payload:
            errors.append('At least one section is required.')

        total_questions = 0
        for si, section in enumerate(sections_payload, start=1):
            section_title = (section.get('title') or '').strip()
            if not section_title:
                errors.append(f'Section {si} title is required.')
            questions = section.get('questions') or []
            if not questions:
                errors.append(f'Section {si} must contain at least one question.')
            for qi, question in enumerate(questions, start=1):
                total_questions += 1
                q_text = (question.get('text') or '').strip()
                q_type = question.get('type')
                options = [str(o).strip() for o in (question.get('options') or []) if str(o).strip()]
                if not q_text:
                    errors.append(f'Section {si} Question {qi} text is required.')
                if q_type not in allowed_types:
                    errors.append(f'Section {si} Question {qi} has invalid type.')
                if q_type in option_types and not options:
                    errors.append(f'Section {si} Question {qi} requires at least one option.')

        if total_questions == 0:
            errors.append('At least one question is required.')

        if errors:
            return JsonResponse({'ok': False, 'errors': errors}, status=400)

        with transaction.atomic():
            if action == 'create':
                item = ChecklistDefinition.objects.create(
                    checklist_id=checklist_code,
                    name=name,
                    checklist_type=checklist_type,
                )
            else:
                item.checklist_id = checklist_code
                item.name = name
                item.checklist_type = checklist_type
                item.save(update_fields=['checklist_id', 'name', 'checklist_type', 'updated_at'])

            item.projects.set(Project.objects.filter(id__in=project_ids, is_active=True))
            item.departments.set(Department.objects.filter(id__in=department_ids, is_active=True))

            existing_questions = {str(q.id): q for q in item.questions.all()}
            incoming_question_ids = set()
            global_order = 1

            for section_data in sections_payload:
                section_title = (section_data.get('title') or '').strip()
                for question_data in section_data.get('questions') or []:
                    qid = str(question_data.get('id') or '')
                    q_options = [str(o).strip() for o in (question_data.get('options') or []) if str(o).strip()]
                    defaults = {
                        'question_text': (question_data.get('text') or '').strip(),
                        'type': question_data.get('type'),
                        'options': q_options,
                        'required': bool(question_data.get('required')),
                        'section': section_title,
                        'order': global_order,
                    }
                    if qid.isdigit() and qid in existing_questions:
                        question_obj = existing_questions[qid]
                        for field, value in defaults.items():
                            setattr(question_obj, field, value)
                        question_obj.save(update_fields=[*defaults.keys(), 'updated_at'])
                    else:
                        question_obj = ChecklistQuestion.objects.create(checklist=item, **defaults)
                    incoming_question_ids.add(question_obj.id)
                    global_order += 1

            item.questions.exclude(id__in=incoming_question_ids).delete()

        return JsonResponse({'ok': True, 'checklist_id': item.id})


    return JsonResponse({'ok': False}, status=400)


def admin_response_action(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == 'POST':
        action = request.POST.get('action')
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if action == 'save_permissions':
            role = request.POST.get('role')
            import json
            permission, _ = RolePermission.objects.get_or_create(role=role)
            permission.visible_columns = json.loads(request.POST.get('visible_columns') or '[]')
            permission.selected_projects = json.loads(request.POST.get('selected_projects') or '[]')
            permission.allowed_actions = json.loads(request.POST.get('allowed_actions') or '[]')
            permission.save()
            return JsonResponse({'ok': True})

        response_id = request.POST.get('response_id')
        response = ChecklistResponse.objects.filter(id=response_id).first()
        if not response:
            return JsonResponse({'ok': False, 'error': 'Response not found'}, status=404)
        if action == 'delete':
            response.delete()
            if is_ajax:
                return JsonResponse({'ok': True})
            return redirect('admin_responses')
        if action == 'toggle':
            response.status = 'Pending' if response.status == 'Rejected' else 'Rejected'
            response.updated_by = request.user
            response.save(update_fields=['status', 'updated_by', 'updated_at'])
            if is_ajax:
                return JsonResponse({'ok': True, 'status': response.status})
            return redirect('admin_responses')
        if action in {'approve', 'reject'}:
            response.status = 'Approved' if action == 'approve' else 'Rejected'
        response.updated_by = request.user
        response.save(update_fields=['status', 'updated_by', 'updated_at'])
        return JsonResponse({'ok': True})

    if request.GET.get('action') == 'view':
        response = ChecklistResponse.objects.select_related('checklist', 'project', 'department', 'submitted_by').prefetch_related(
            'answers__question',
        ).filter(id=request.GET.get('response_id')).first()
        if not response:
            return JsonResponse({'ok': False}, status=404)
        return JsonResponse({
            'checklist_id': response.checklist.checklist_id,
            'checklist_name': response.checklist.name,
            'submitted_by': response.submitted_by.username if response.submitted_by else '',
            'answers': [{
                'question': answer.question.question_text,
                'answer_text': answer.answer_text,
                'file_url': answer.file.url if answer.file else '',
            } for answer in response.answers.all()],
        })

    return JsonResponse({'ok': False}, status=400)


def admin_master_create(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        if request.POST.get("form_type") == "user":
            username = (request.POST.get('username') or '').strip()
            password = request.POST.get('password') or ''
            email = _clean_email_or_error(request, request.POST.get('email'))
            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect('admin_users')
            if email is None:
                return redirect('admin_users')
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose another.")
                return redirect('admin_users')

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                email=email,
            )

            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role'),
                department_id=request.POST.get('department') or None,
                project_id=request.POST.get('project') or None,
                is_active=True,
            )
        elif request.POST.get("form_type") == "department":
            code = (request.POST.get('code') or '').strip()
            name = (request.POST.get('name') or '').strip()
            is_active = request.POST.get('is_active') == 'true'

            if not code or not name:
                messages.error(request, "Department code and name are required.")
                return redirect('admin_departments')

            if Department.objects.filter(code=code).exists():
                messages.error(request, "Department code already exists.")
                return redirect('admin_departments')

            Department.objects.create(code=code, name=name, is_active=is_active)
        elif request.POST.get("form_type") == "project":
            code = (request.POST.get('code') or '').strip()
            name = (request.POST.get('name') or '').strip()
            domain = request.POST.get('domain')
            is_active = request.POST.get('is_active') == 'true'

            if not code or not name or not domain:
                messages.error(request, "Project code, name and domain are required.")
                return redirect('admin_projects')

            if domain not in {'Corporate', 'Non-Corporate'}:
                messages.error(request, "Invalid project domain.")
                return redirect('admin_projects')

            if Project.objects.filter(code=code).exists():
                messages.error(request, "Project code already exists.")
                return redirect('admin_projects')

            Project.objects.create(code=code, name=name, domain=domain, is_active=is_active)

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('admin_dashboard')


def admin_master_create_legacy(request):
    if request.method == "POST":
        return admin_master_create(request)
    return redirect('admin_master_create')


def admin_user_action(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')

        if action in {'delete', 'toggle'} and user_id:
            if action == 'delete':
                User.objects.filter(id=user_id).delete()
            else:
                try:
                    profile_obj = UserProfile.objects.get(user_id=user_id)
                    profile_obj.is_active = not profile_obj.is_active
                    profile_obj.save()
                except UserProfile.DoesNotExist:
                    messages.error(request, "User profile not found.")
            return redirect('admin_users')

    if request.GET.get('action') == "view":
        user_id = request.GET.get('id')

        profile_obj = UserProfile.objects.select_related(
            'user', 'department', 'project',
        ).get(user__id=user_id)

        return JsonResponse({
            "username": profile_obj.user.username,
            "first_name": profile_obj.user.first_name,
            "last_name": profile_obj.user.last_name,
            "role": profile_obj.role,
            "department_id": profile_obj.department.id if profile_obj.department else "",
            "project_id": profile_obj.project.id if profile_obj.project else "",
            "status": profile_obj.is_active,
        })

    if request.method == "POST":
        edit_id = request.POST.get('edit_id')

        if edit_id:
            try:
                profile_obj = UserProfile.objects.get(user__id=edit_id)
            except UserProfile.DoesNotExist:
                return redirect('admin_users')

            user = profile_obj.user
            username = (request.POST.get('username') or '').strip()
            if not username:
                messages.error(request, "Username is required.")
                return redirect('admin_users')
            if User.objects.filter(username=username).exclude(id=user.id).exists():
                messages.error(request, "Username already exists. Please choose another.")
                return redirect('admin_users')

            user.username = username
            email = _clean_email_or_error(request, request.POST.get('email'))
            if email is None:
                return redirect('admin_users')

            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = email
            password = request.POST.get('password')
            if password:
                user.set_password(password)
            user.save()

            profile_obj.role = request.POST.get('role')
            profile_obj.department_id = request.POST.get('department') or None
            profile_obj.project_id = request.POST.get('project') or None
            profile_obj.save()

            return redirect('admin_users')

    return redirect('admin_users')


def admin_department_action(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get('action')
        department_id = request.POST.get('department_id')

        if action == 'delete' and department_id:
            Department.objects.filter(id=department_id).delete()
            return redirect('admin_departments')

        if action == 'edit' and department_id:
            department = Department.objects.filter(id=department_id).first()
            if not department:
                messages.error(request, "Department not found.")
                return redirect('admin_departments')

            code = (request.POST.get('code') or '').strip()
            name = (request.POST.get('name') or '').strip()
            is_active = request.POST.get('is_active') == 'true'

            if not code or not name:
                messages.error(request, "Department code and name are required.")
                return redirect('admin_departments')

            if Department.objects.filter(code=code).exclude(id=department.id).exists():
                messages.error(request, "Department code already exists.")
                return redirect('admin_departments')

            department.code = code
            department.name = name
            department.is_active = is_active
            department.save()
            return redirect('admin_departments')

    return redirect('admin_departments')


def admin_project_action(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get('action')
        project_id = request.POST.get('project_id')

        if action == 'delete' and project_id:
            Project.objects.filter(id=project_id).delete()
            return redirect('admin_projects')

        if action == 'edit' and project_id:
            project = Project.objects.filter(id=project_id).first()
            if not project:
                messages.error(request, "Project not found.")
                return redirect('admin_projects')

            code = (request.POST.get('code') or '').strip()
            name = (request.POST.get('name') or '').strip()
            domain = request.POST.get('domain')
            is_active = request.POST.get('is_active') == 'true'

            if not code or not name or not domain:
                messages.error(request, "Project code, name and domain are required.")
                return redirect('admin_projects')

            if domain not in {'Corporate', 'Non-Corporate'}:
                messages.error(request, "Invalid project domain.")
                return redirect('admin_projects')

            if Project.objects.filter(code=code).exclude(id=project.id).exists():
                messages.error(request, "Project code already exists.")
                return redirect('admin_projects')

            project.code = code
            project.name = name
            project.domain = domain
            project.is_active = is_active
            project.save()
            return redirect('admin_projects')

    return redirect('admin_projects')
