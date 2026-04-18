from django.shortcuts import render, redirect, get_object_or_404
from .models import Checklist, Question, ChecklistTransaction, Answer, UserProfile, Department, Project
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
import uuid

# =========================================================
# COMMON HELPER
# =========================================================
def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    return UserProfile.objects.filter(user=user).first()


# =========================================================
# HOME
# =========================================================
def home(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)

    if not profile:
        return redirect('login')

    if profile.role == "HOD":
        return redirect('hod_dashboard')

    elif profile.role == "Admin":
        return redirect('admin_dashboard')

    elif profile.role == "Management":
        return redirect('management_dashboard')

    checklists = Checklist.objects.filter(department=profile.department)
    transactions = ChecklistTransaction.objects.all().order_by('-submitted_date')[:10]

    return render(request, 'home.html', {
        'checklists': checklists,
        'transactions': transactions
    })


# =========================================================
# AUTH
# =========================================================
def user_login(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":

        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)

            profile = get_user_profile(user)

            if profile:
                if profile.role == "HOD":
                    return redirect('hod_dashboard')
                elif profile.role == "Admin":
                    return redirect('admin_dashboard')
                elif profile.role == "Management":
                    return redirect('management_dashboard')

            return redirect('home')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')


# =========================================================
# CHECKLIST
# =========================================================
def checklist_detail(request, checklist_id):

    if not request.user.is_authenticated:
        return redirect('login')

    checklist = get_object_or_404(Checklist, id=checklist_id)
    questions = Question.objects.filter(checklist=checklist)

    if request.method == "POST":

        txn = ChecklistTransaction.objects.create(
            transaction_id=str(uuid.uuid4()),
            checklist=checklist,
            user=request.user,
            project=checklist.project,
            department=checklist.department
        )

        for q in questions:
            val = request.POST.get(f"q{q.id}")
            if val:
                Answer.objects.create(
                    transaction=txn,
                    question=q,
                    answer=val
                )

        return redirect('home')

    return render(request, 'checklist_detail.html', {
        'checklist': checklist,
        'questions': questions
    })


# =========================================================
# HOD
# =========================================================
def hod_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)

    if not profile or profile.role != "HOD":
        return redirect('home')

    txns = ChecklistTransaction.objects.filter(
        department=profile.department
    ).order_by('-submitted_date')

    return render(request, 'hod_dashboard.html', {'transactions': txns})


def update_status(request, txn_id, action):

    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)

    if not profile or profile.role != "HOD":
        return redirect('home')

    txn = get_object_or_404(ChecklistTransaction, id=txn_id)

    if txn.department != profile.department:
        return redirect('home')

    if action == "approve":
        txn.status = "Approved"
    elif action == "reject":
        txn.status = "Rejected"

    txn.approved_by = request.user
    txn.approval_date = timezone.now()
    txn.save()

    return redirect('hod_dashboard')


# =========================================================
# VIEW
# =========================================================
def view_checklist(request, txn_id):

    if not request.user.is_authenticated:
        return redirect('login')

    txn = get_object_or_404(ChecklistTransaction, id=txn_id)
    profile = get_user_profile(request.user)

    if profile and profile.role == "User" and txn.user != request.user:
        return redirect('home')

    answers = Answer.objects.filter(transaction=txn)

    return render(request, 'view_checklist.html', {
        'txn': txn,
        'answers': answers
    })


def my_submissions(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)

    if profile.role == "HOD":
        txns = ChecklistTransaction.objects.filter(department=profile.department)
    else:
        txns = ChecklistTransaction.objects.filter(user=request.user)

    return render(request, 'my_submissions.html', {
        'transactions': txns.order_by('-submitted_date')
    })


# =========================================================
# ADMIN DASHBOARD
# =========================================================
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
        'rejected': txns.filter(status="Rejected").count()
    })


from django.db.models import Count, Q # Q ka use complex filtering ke liye hota hai

# =========================================================
# ADMIN USERS 
# =========================================================
def admin_users(request):
    # Check if user is logged in
    if not request.user.is_authenticated:
        return redirect('login')

    # Fetch user profile and check for Admin role
    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    # --- GET FILTER PARAMETERS ---
    search_query = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')
    proj_filter = request.GET.get('project', '')
    stat_filter = request.GET.get('status', '')

    # --- INITIAL QUERYSET ---
    # select_related se database queries kam ho jati hain (Joins use hote hain)
    user_list = UserProfile.objects.select_related('user', 'department', 'project')

    # --- APPLY SEARCH & FILTERS ---
    if search_query:
        user_list = user_list.filter(
            Q(user__username__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query)
        )
    if dept_filter:
        user_list = user_list.filter(department_id=dept_filter)
    if proj_filter:
        user_list = user_list.filter(project_id=proj_filter)
    if stat_filter:
        is_active = True if stat_filter == 'active' else False
        user_list = user_list.filter(is_active=is_active)

    # --- CALCULATE DYNAMIC COUNTS FOR CARDS ---
    # Role-based counts (Top Right Cards)
    role_counts = {
        'user': user_list.filter(role='User').count(),
        'hod': user_list.filter(role='HOD').count(),
        'management': user_list.filter(role='Management').count(),
    }

    # Status counts (For Pie Chart)
    total_active = user_list.filter(is_active=True).count()
    total_inactive = user_list.filter(is_active=False).count()

    # --- DEPARTMENT-WISE DATA (For Stacked Bar Chart) ---
    # Isme har department ke liye Active aur Inactive users ka count nikal rahe hain
    dept_stats = Department.objects.annotate(
        active_count=Count('userprofile', filter=Q(userprofile__is_active=True)),
        inactive_count=Count('userprofile', filter=Q(userprofile__is_active=False))
    )

    # Convert stats to lists for Chart.js
    dept_labels = [d.name for d in dept_stats]
    dept_active_data = [d.active_count for d in dept_stats]
    dept_inactive_data = [d.inactive_count for d in dept_stats]

    # --- CONTEXT DATA ---
    context = {
        'users': user_list,
        'departments': Department.objects.all(),
        'projects': Project.objects.all(),
        
        # Dashboard stats
        'role_counts': role_counts,
        'active_users': total_active,
        'inactive_users': total_inactive,
        
        # Chart lists (JSON format for JS)
        'dept_labels': dept_labels,
        'dept_active_data': dept_active_data,
        'dept_inactive_data': dept_inactive_data,
    }

    return render(request, 'admin_panel/admin_users.html', context)

# =========================================================
# ADMIN DEPARTMENTS
# =========================================================
def admin_departments(request):
    return render(request, 'admin_panel/admin_departments.html', {
        'departments': Department.objects.all()
    })


# =========================================================
# ADMIN PROJECTS
# =========================================================
def admin_projects(request):
    return render(request, 'admin_panel/admin_projects.html', {
        'projects': Project.objects.all()
    })


# =========================================================
# ADMIN CHECKLISTS
# =========================================================
def admin_checklists(request):
    return render(request, 'admin_panel/admin_checklists.html', {
        'checklists': Checklist.objects.all()
    })


# =========================================================
# ADMIN RESPONSES
# =========================================================
def admin_responses(request):
    return render(request, 'admin_panel/admin_responses.html', {
        'transactions': ChecklistTransaction.objects.all()
    })


# =========================================================
# MANAGEMENT DASHBOARD
# =========================================================
def management_dashboard(request):
    return render(request, 'management_dashboard.html')


# =========================================================
# UNIVERSAL CREATE
# =========================================================
def admin_master_create(request):

    if request.method == "POST":

        if request.POST.get("form_type") == "user":

            user = User.objects.create_user(
                username=request.POST.get('username'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name')
            )

            UserProfile.objects.create(
                user=user,
                role=request.POST.get('role'),
                department_id=request.POST.get('department') or None,
                project_id=request.POST.get('project') or None,
                is_active=True
            )

        return redirect(request.META.get('HTTP_REFERER'))

    return redirect('admin_dashboard')


# =========================================================
# ADMIN USER ACTION (FINAL)
# =========================================================
from django.http import JsonResponse

def admin_user_action(request):

    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Admin":
        return redirect('home')

    # DELETE
    delete_id = request.GET.get('delete')
    if delete_id:
        User.objects.filter(id=delete_id).delete()
        return redirect('admin_users')

    # TOGGLE
    toggle_id = request.GET.get('toggle')
    if toggle_id:
        profile_obj = UserProfile.objects.get(user_id=toggle_id)
        profile_obj.is_active = not profile_obj.is_active
        profile_obj.save()
        return redirect('admin_users')

    # ================= VIEW =================
    if request.GET.get('action') == "view":
        user_id = request.GET.get('id')

        profile_obj = UserProfile.objects.select_related(
            'user', 'department', 'project'
        ).get(user__id=user_id)

        return JsonResponse({
            "username": profile_obj.user.username,
            "first_name": profile_obj.user.first_name,
            "last_name": profile_obj.user.last_name,
            "role": profile_obj.role,
            "department_id": profile_obj.department.id if profile_obj.department else "",
            "project_id": profile_obj.project.id if profile_obj.project else "",
            "status": profile_obj.is_active
        })

# ================= EDIT =================
    if request.method == "POST":

        edit_id = request.POST.get('edit_id')

        if edit_id:
            try:
                profile_obj = UserProfile.objects.get(user__id=edit_id)
            except UserProfile.DoesNotExist:
                return redirect('admin_users')

            user = profile_obj.user

            # UPDATE USER
            user.username = request.POST.get('username')
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.save()

            # UPDATE PROFILE
            profile_obj.role = request.POST.get('role')
            profile_obj.department_id = request.POST.get('department') or None
            profile_obj.project_id = request.POST.get('project') or None
            profile_obj.save()

            return redirect('admin_users')