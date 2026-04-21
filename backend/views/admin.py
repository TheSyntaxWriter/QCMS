from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render

from ..models import Checklist, ChecklistTransaction, Department, Project, UserProfile
from .common import get_user_profile


def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    txns = ChecklistTransaction.objects.all()

    return render(request, 'admin_panel/admin_dashboard.html', {
        'transactions': txns,
        'total_users': UserProfile.objects.count(),
        'total_checklists': Checklist.objects.count(),
        'pending': txns.filter(status="Pending").count(),
        'approved': txns.filter(status="Approved").count(),
        'rejected': txns.filter(status="Rejected").count(),
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

    return render(request, 'admin_panel/admin_departments.html', {
        'departments': Department.objects.all(),
    })


def admin_projects(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    return render(request, 'admin_panel/admin_projects.html', {
        'projects': Project.objects.all(),
    })


def admin_checklists(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    return render(request, 'admin_panel/admin_checklists.html', {
        'checklists': Checklist.objects.all(),
    })


def admin_responses(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    return render(request, 'admin_panel/admin_responses.html', {
        'transactions': ChecklistTransaction.objects.all(),
    })


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
            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect('admin_users')
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists. Please choose another.")
                return redirect('admin_users')

            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
            )

            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role'),
                department_id=request.POST.get('department') or None,
                project_id=request.POST.get('project') or None,
                is_active=True,
            )

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
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
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
