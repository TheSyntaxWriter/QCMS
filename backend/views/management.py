from django.shortcuts import redirect, render

from .common import get_user_profile


def management_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "Management":
        return redirect('home')

    return render(request, 'management_dashboard.html')
