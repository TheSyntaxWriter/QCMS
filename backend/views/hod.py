from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import ChecklistTransaction
from .common import get_user_profile


def hod_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "HOD":
        return redirect('home')

    txns = ChecklistTransaction.objects.filter(
        department=profile.department,
    ).order_by('-submitted_date')

    return render(request, 'hod_dashboard.html', {'transactions': txns})


def update_status(request, txn_id):
    if not request.user.is_authenticated:
        return redirect('login')

    if request.method != 'POST':
        return redirect('hod_dashboard')

    profile = get_user_profile(request.user)
    if not profile or profile.role != "HOD":
        return redirect('home')

    txn = get_object_or_404(ChecklistTransaction, id=txn_id)

    if txn.department != profile.department:
        return redirect('home')

    action = request.POST.get('action')

    if action == "approve":
        txn.status = "Approved"
    elif action == "reject":
        txn.status = "Rejected"

    txn.approved_by = request.user
    txn.approval_date = timezone.now()
    txn.save()

    return redirect('hod_dashboard')
