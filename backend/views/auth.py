from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render

from .common import get_user_profile, redirect_for_profile, safe_next_url
from ..logging_service import write_activity_log
from ..models import ActivityLog


def home(request):

    # User not logged in
    if not request.user.is_authenticated:
        return redirect('login')

    # Redirect based on role/profile
    return redirect_for_profile(
        get_user_profile(request.user),
        request.user
    )


def user_login(request):

    # Already logged in
    if request.user.is_authenticated:
        next_url = safe_next_url(request)
        if next_url:
            return redirect(next_url)

        return redirect_for_profile(
            get_user_profile(request.user),
            request.user
        )

    # Login form submit
    if request.method == "POST":

        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )

        # Login success
        if user:

            login(request, user)
            request.session.cycle_key()

            write_activity_log(
                action_type='Login Success',
                module_name='Authentication',
                description=f'User {user.username} logged in successfully.',
                status=ActivityLog.STATUS_SUCCESS,
                user=user,
            )

            next_url = safe_next_url(request)
            if next_url:
                return redirect(next_url)

            return redirect_for_profile(
                get_user_profile(user),
                user
            )

        # Login failed
        write_activity_log(
            action_type='Login Failure',
            module_name='Authentication',
            description=f"Failed login attempt for username '{request.POST.get('username') or ''}'.",
            status=ActivityLog.STATUS_FAILED,
            user=request.user,
        )

        return render(
            request,
            'login.html',
            {'error': 'Invalid credentials', 'next': safe_next_url(request)}
        )

    return render(request, 'login.html', {'next': safe_next_url(request)})


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

    return redirect('login')
