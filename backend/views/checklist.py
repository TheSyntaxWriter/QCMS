import uuid

from django.shortcuts import get_object_or_404, redirect, render

from ..models import Answer, Checklist, ChecklistTransaction, Question
from .common import get_user_profile


def checklist_detail(request, checklist_id):
    if not request.user.is_authenticated:
        return redirect('login')

    checklist = get_object_or_404(Checklist, id=checklist_id)
    questions = Question.objects.filter(checklist=checklist)

    if request.method == "POST":
        txn = ChecklistTransaction.objects.create(
            transaction_id=str(uuid.uuid4()),
            checklist=checklist,
            user=request.user,
            project=checklist.project,
            department=checklist.department,
        )

        for question in questions:
            val = request.POST.get(f"q{question.id}")
            if val:
                Answer.objects.create(
                    transaction=txn,
                    question=question,
                    answer=val,
                )

        return redirect('home')

    return render(request, 'checklist_detail.html', {
        'checklist': checklist,
        'questions': questions,
    })


def view_checklist(request, txn_id):
    if not request.user.is_authenticated:
        return redirect('login')

    txn = get_object_or_404(ChecklistTransaction, id=txn_id)
    profile = get_user_profile(request.user)

    if profile and profile.role == "User" and txn.user != request.user:
        return redirect('home')

    answers = Answer.objects.filter(transaction=txn)

    return render(request, 'view_checklist.html', {
        'txn': txn,
        'answers': answers,
    })


def my_submissions(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = get_user_profile(request.user)

    if profile.role == "HOD":
        txns = ChecklistTransaction.objects.filter(department=profile.department)
    else:
        txns = ChecklistTransaction.objects.filter(user=request.user)

    return render(request, 'my_submissions.html', {
        'transactions': txns.order_by('-submitted_date'),
    })
