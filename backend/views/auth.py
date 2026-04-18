from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from ..models import Checklist, ChecklistTransaction
from .common import get_user_profile


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile:
        return redirect('login')

    if profile.role == "HOD":
        return redirect('hod_dashboard')
    if profile.role == "Admin":
        return redirect('admin_dashboard')
    if profile.role == "Management":
        return redirect('management_dashboard')

    checklists = Checklist.objects.filter(department=profile.department)
    transactions = ChecklistTransaction.objects.all().order_by('-submitted_date')[:10]

    return render(request, 'home.html', {
        'checklists': checklists,
        'transactions': transactions,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )

        if user:
            login(request, user)
            profile = get_user_profile(user)

            if profile:
                if profile.role == "HOD":
                    return redirect('hod_dashboard')
                if profile.role == "Admin":
                    return redirect('admin_dashboard')
                if profile.role == "Management":
                    return redirect('management_dashboard')

            return redirect('home')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')
