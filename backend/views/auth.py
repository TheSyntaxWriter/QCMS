from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .common import get_user_profile, redirect_for_profile


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return redirect_for_profile(get_user_profile(request.user))


def user_login(request):
    if request.user.is_authenticated:
        return redirect_for_profile(get_user_profile(request.user))

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )

        if user:
            login(request, user)
            return redirect_for_profile(get_user_profile(user))

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect('login')
