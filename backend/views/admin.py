from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

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

    role_counts = {
        'user': user_list.filter(role='User').count(),
        'hod': user_list.filter(role='HOD').count(),
        'management': user_list.filter(role='Management').count(),
    }

    total_active = user_list.filter(is_active=True).count()
    total_inactive = user_list.filter(is_active=False).count()

    dept_stats = Department.objects.annotate(
        active_count=Count('userprofile', filter=Q(userprofile__is_active=True)),
        inactive_count=Count('userprofile', filter=Q(userprofile__is_active=False)),
    )

    dept_labels = [department.name for department in dept_stats]
    dept_active_data = [department.active_count for department in dept_stats]
    dept_inactive_data = [department.inactive_count for department in dept_stats]

    context = {
        'users': user_list,
        'departments': Department.objects.all(),
        'projects': Project.objects.all(),
        'role_counts': role_counts,
        'active_users': total_active,
        'inactive_users': total_inactive,
        'dept_labels': dept_labels,
        'dept_active_data': dept_active_data,
        'dept_inactive_data': dept_inactive_data,
    }

    return render(request, 'admin_panel/admin_users.html', context)


def admin_departments(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            Department.objects.create(
                code=request.POST.get("code"),
                name=request.POST.get("name"),
                is_active=bool(request.POST.get("is_active")),
            )
            return redirect('admin_departments')

        if action == "update":
            department = get_object_or_404(Department, id=request.POST.get("department_id"))
            department.code = request.POST.get("code")
            department.name = request.POST.get("name")
            department.is_active = bool(request.POST.get("is_active"))
            department.save()
            return redirect('admin_departments')

        if action == "delete":
            Department.objects.filter(id=request.POST.get("department_id")).delete()
            return redirect('admin_departments')

    edit_department = None
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_department = get_object_or_404(Department, id=edit_id)

    return render(request, 'admin_panel/admin_departments.html', {
        'departments': Department.objects.all().order_by('name'),
        'edit_department': edit_department,
    })


def admin_projects(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            Project.objects.create(
                code=request.POST.get("code"),
                name=request.POST.get("name"),
                domain=request.POST.get("domain"),
                is_active=bool(request.POST.get("is_active")),
            )
            return redirect('admin_projects')

        if action == "update":
            project = get_object_or_404(Project, id=request.POST.get("project_id"))
            project.code = request.POST.get("code")
            project.name = request.POST.get("name")
            project.domain = request.POST.get("domain")
            project.is_active = bool(request.POST.get("is_active"))
            project.save()
            return redirect('admin_projects')

        if action == "delete":
            Project.objects.filter(id=request.POST.get("project_id")).delete()
            return redirect('admin_projects')

    edit_project = None
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_project = get_object_or_404(Project, id=edit_id)

    return render(request, 'admin_panel/admin_projects.html', {
        'projects': Project.objects.all().order_by('name'),
        'edit_project': edit_project,
        'domains': ['Corporate', 'Non-Corporate'],
    })


def admin_checklists(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "create":
            Checklist.objects.create(
                code=request.POST.get("code"),
                name=request.POST.get("name"),
                checklist_type=request.POST.get("checklist_type"),
                project_id=request.POST.get("project_id") or None,
                department_id=request.POST.get("department_id") or None,
                is_active=bool(request.POST.get("is_active")),
            )
            return redirect('admin_checklists')

        if action == "update":
            checklist = get_object_or_404(Checklist, id=request.POST.get("checklist_id"))
            checklist.code = request.POST.get("code")
            checklist.name = request.POST.get("name")
            checklist.checklist_type = request.POST.get("checklist_type")
            checklist.project_id = request.POST.get("project_id") or None
            checklist.department_id = request.POST.get("department_id") or None
            checklist.is_active = bool(request.POST.get("is_active"))
            checklist.save()
            return redirect('admin_checklists')

        if action == "delete":
            Checklist.objects.filter(id=request.POST.get("checklist_id")).delete()
            return redirect('admin_checklists')

    edit_checklist = None
    edit_id = request.GET.get("edit")
    if edit_id:
        edit_checklist = get_object_or_404(Checklist, id=edit_id)

    return render(request, 'admin_panel/admin_checklists.html', {
        'checklists': Checklist.objects.select_related('department', 'project').all().order_by('name'),
        'departments': Department.objects.all().order_by('name'),
        'projects': Project.objects.all().order_by('name'),
        'checklist_types': ['Daily', 'Weekly', 'Monthly', 'Activity'],
        'edit_checklist': edit_checklist,
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
            user = User.objects.create_user(
                username=request.POST.get('username'),
                password=request.POST.get('password'),
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


def admin_user_action(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    delete_id = request.GET.get('delete')
    if delete_id:
        User.objects.filter(id=delete_id).delete()
        return redirect('admin_users')

    toggle_id = request.GET.get('toggle')
    if toggle_id:
        profile_obj = UserProfile.objects.get(user_id=toggle_id)
        profile_obj.is_active = not profile_obj.is_active
        profile_obj.save()
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
            user.username = request.POST.get('username')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()

            profile_obj.role = request.POST.get('role')
            profile_obj.department_id = request.POST.get('department') or None
            profile_obj.project_id = request.POST.get('project') or None
            profile_obj.save()

            return redirect('admin_users')
