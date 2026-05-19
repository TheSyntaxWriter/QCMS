from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .common import get_user_profile, redirect_for_profile, resolve_post_login_url
from ..logging_service import write_activity_log
from ..models import ActivityLog


def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return redirect(resolve_post_login_url(request.user, profile=get_user_profile(request.user)))


def user_login(request):
    # Authenticated users should never see login again; send them to a safe home page.
    if request.user.is_authenticated:
        return redirect(resolve_post_login_url(request.user, profile=get_user_profile(request.user)))

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )

        if user:
            login(request, user)
            write_activity_log(
                action_type='Login Success',
                module_name='Authentication',
                description=f'User {user.username} logged in successfully.',
                status=ActivityLog.STATUS_SUCCESS,
                user=user,
            )
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect(resolve_post_login_url(user, profile=get_user_profile(user)))

        write_activity_log(
            action_type='Login Failure',
            module_name='Authentication',
            description=f"Failed login attempt for username '{request.POST.get('username') or ''}'.",
            status=ActivityLog.STATUS_FAILED,
            user=request.user,
        )
        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def user_logout(request):
    if request.user.is_authenticated:
        write_activity_log(
            action_type='Logout',
            module_name='Authentication',
            description=f'User {request.user.username} logged out.',
            status=ActivityLog.STATUS_INFO,
            user=request.user,
        )
    logout(request)
    request.session.flush()
    return redirect('login')
