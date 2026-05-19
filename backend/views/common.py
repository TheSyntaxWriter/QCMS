from django.shortcuts import redirect
from django.urls import reverse

from ..models import UserProfile


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    return UserProfile.objects.filter(user=user).first()


def resolve_post_login_url(user, profile=None):
    """Return the safe authenticated landing URL for the current user.

    The login redirect loop happened when an authenticated user had no UserProfile:
    both `/login/` and `/` redirected back to each other. We break that loop by
    always returning an authenticated destination for logged-in users.
    """
    if user and getattr(user, 'is_authenticated', False):
        profile = profile if profile is not None else get_user_profile(user)

        if profile:
            if profile.role in {'User', 'HOD'}:
                return reverse('my_checklists')
            if profile.role == 'Management':
                return reverse('dashboard')
            if profile.role == 'Admin':
                return reverse('admin_dashboard')

        # Fallback for superusers/admin users that do not have UserProfile yet.
        if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
            return reverse('admin_dashboard')

        # Generic authenticated fallback that never points to login.
        return reverse('my_checklists')

    return reverse('login')


def redirect_for_profile(profile, user=None):
    if user and getattr(user, 'is_authenticated', False):
        return redirect(resolve_post_login_url(user, profile=profile))

    # Preserve historical behaviour for call sites that only pass profile.
    if profile:
        role = profile.role
        if role in {'User', 'HOD'}:
            return redirect('my_checklists')
        if role == 'Management':
            return redirect('dashboard')
        if role == 'Admin':
            return redirect('admin_dashboard')
    return redirect('login')
