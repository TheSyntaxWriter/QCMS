from django.shortcuts import redirect

from ..models import UserProfile


def get_user_profile(user):
    if not user or not user.is_authenticated:
        return None
    return UserProfile.objects.filter(user=user).first()


def redirect_for_profile(profile):
    if not profile:
        return redirect('login')

    if profile.role in {'User', 'HOD'}:
        return redirect('my_checklists')
    if profile.role == 'Management':
        return redirect('dashboard')
    if profile.role == 'Admin':
        return redirect('admin_dashboard')
    return redirect('login')
