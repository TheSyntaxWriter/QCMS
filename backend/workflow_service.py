from __future__ import annotations

from dataclasses import dataclass


class ResponseStatus:
    # Current active statuses
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

    # Future-ready statuses (not yet fully exposed in UI)
    WIP = 'WIP'
    PENDING_APPROVAL = 'Pending for Approval'

    CHOICES = (
        (WIP, WIP),
        (PENDING_APPROVAL, PENDING_APPROVAL),
        (PENDING, PENDING),
        (APPROVED, APPROVED),
        (REJECTED, REJECTED),
    )


STATUS_TRANSITIONS = {
    ResponseStatus.WIP: {ResponseStatus.PENDING_APPROVAL},
    ResponseStatus.PENDING_APPROVAL: {ResponseStatus.APPROVED, ResponseStatus.REJECTED, ResponseStatus.WIP},
    # Backward-compatible transitions for current production status set.
    ResponseStatus.PENDING: {ResponseStatus.APPROVED, ResponseStatus.REJECTED},
    ResponseStatus.APPROVED: set(),
    ResponseStatus.REJECTED: {ResponseStatus.PENDING, ResponseStatus.WIP},
}


ACTION_TO_TARGET_STATUS = {
    'approve': ResponseStatus.APPROVED,
    'reject': ResponseStatus.REJECTED,
}


@dataclass(frozen=True)
class WorkflowDecision:
    allowed: bool
    reason: str = ''
    next_status: str | None = None


def can_transition_response(current_status: str, target_status: str) -> bool:
    return target_status in STATUS_TRANSITIONS.get(current_status, set())


def evaluate_status_action(current_status: str, action: str) -> WorkflowDecision:
    if action not in ACTION_TO_TARGET_STATUS:
        return WorkflowDecision(False, reason='Unsupported status action')

    target = ACTION_TO_TARGET_STATUS[action]

    if not target:
        return WorkflowDecision(False, reason='Unable to resolve target status')

    if not can_transition_response(current_status, target):
        return WorkflowDecision(False, reason=f'Transition blocked: {current_status} -> {target}')

    return WorkflowDecision(True, next_status=target)


def can_edit_response(response, user, role: str) -> bool:
    if role == 'Admin':
        return True
    owner_id = getattr(response, 'submitted_by_id', None)
    if owner_id != getattr(user, 'id', None):
        return False
    return getattr(response, 'status', '') in {ResponseStatus.WIP, ResponseStatus.REJECTED}


def can_submit_response(response, user, role: str) -> bool:
    if role == 'Admin':
        return True
    owner_id = getattr(response, 'submitted_by_id', None)
    if owner_id != getattr(user, 'id', None):
        return False
    return getattr(response, 'status', '') in {ResponseStatus.WIP, ResponseStatus.REJECTED}


def _can_hod_decide_response(response, user) -> bool:
    return getattr(response, 'hod_id', None) == getattr(user, 'id', None)


def can_approve_response(response, role: str, user=None) -> bool:
    if not evaluate_status_action(response.status, 'approve').allowed:
        return False
    if role in {'Admin', 'Management'}:
        return True
    return role == 'HOD' and _can_hod_decide_response(response, user)


def can_reject_response(response, role: str, user=None) -> bool:
    if not evaluate_status_action(response.status, 'reject').allowed:
        return False
    if role in {'Admin', 'Management'}:
        return True
    return role == 'HOD' and _can_hod_decide_response(response, user)
