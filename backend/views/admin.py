from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.http import JsonResponse
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
            password = request.POST.get('password')
            if password:
                user.set_password(password)
            user.save()

            profile_obj.role = request.POST.get('role')
            profile_obj.department_id = request.POST.get('department') or None
            profile_obj.project_id = request.POST.get('project') or None
            profile_obj.save()

            return redirect('admin_users')
