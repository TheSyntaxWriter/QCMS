from django.shortcuts import redirect

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