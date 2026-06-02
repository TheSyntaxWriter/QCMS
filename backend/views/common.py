from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from ..models import UserProfile


def get_user_profile(user):

    if not user or not user.is_authenticated:
        return None

    return UserProfile.objects.filter(user=user).first()


def redirect_for_profile(profile, user=None):
    """
    Centralized safe redirect logic.
    """

    # Django superuser
    if user and user.is_superuser:
        return redirect('/admin/')

    # No profile fallback
    if not profile:
        return redirect('my_checklists')

    # QCMS Admin
    if profile.role == 'Admin':
        return redirect('admin_dashboard')

    # Management
    if profile.role == 'Management':
        return redirect('dashboard')

    # User / HOD
    if profile.role in {'User', 'HOD'}:
        return redirect('my_checklists')

    # Safe fallback
    return redirect('my_checklists')


def safe_next_url(request):
    """Return a safe local next URL, or None."""
    next_url = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if not next_url:
        return None
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return next_url
    return None
