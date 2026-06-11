import json
from io import BytesIO

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from pypdf import PdfWriter

from .upload_validation import MAX_CHECKLIST_UPLOAD_SIZE, validate_branding_upload, validate_checklist_upload
from .models import (
    Checklist,
    ChecklistAnswer,
    ChecklistDefinition,
    ChecklistQuestion,
    ChecklistResponse,
    ChecklistType,
    Department,
    Project,
    Question,
    ResponseDecision,
    RolePermission,
    Section,
    UserProfile,
)
from .workflow_service import ResponseStatus


class AccessControlTests(TestCase):
    def create_user_with_role(self, username, role):
        user = User.objects.create_user(username=username, password="pass12345")
        UserProfile.objects.create(user=user, role=role)
        return user

    def test_admin_pages_require_login(self):
        admin_urls = [
            "admin_dashboard",
            "admin_departments",
            "admin_projects",
            "admin_checklists",
            "admin_responses",
            "admin_create",
        ]

        for url_name in admin_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                if url_name == "admin_create":
                    self.assertRedirects(response, reverse("admin_master_create"), fetch_redirect_response=False)
                else:
                    self.assertRedirects(response, reverse("login"))

    def test_admin_pages_reject_non_admin_users(self):
        user = self.create_user_with_role("basic_user", "User")
        self.client.force_login(user)

        admin_urls = [
            "admin_dashboard",
            "admin_departments",
            "admin_projects",
            "admin_checklists",
            "admin_responses",
            "admin_create",
        ]

        for url_name in admin_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                expected = reverse("admin_master_create") if url_name == "admin_create" else reverse("home")
                self.assertRedirects(response, expected, fetch_redirect_response=False)

    def test_dashboard_access_control(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("login"))

        user = self.create_user_with_role("hod_user", "HOD")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("my_checklists"))

        management_user = self.create_user_with_role("mgmt_user", "Management")
        self.client.force_login(management_user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        legacy_response = self.client.get(reverse("management_dashboard"))
        self.assertRedirects(legacy_response, reverse("dashboard"))

    def test_home_redirects_by_role(self):
        role_expected = {
            'User': 'my_checklists',
            'HOD': 'my_checklists',
            'Management': 'dashboard',
            'Admin': 'admin_dashboard',
        }
        for role, expected in role_expected.items():
            user = self.create_user_with_role(f'{role.lower()}_user', role)
            self.client.force_login(user)
            response = self.client.get(reverse('home'))
            self.assertRedirects(response, reverse(expected))
            self.client.logout()


class ChecklistBuilderTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="builder_admin", password="pass12345")
        UserProfile.objects.create(user=self.admin_user, role="Admin")
        self.client.force_login(self.admin_user)
        self.checklist_type = ChecklistType.objects.create(name="Safety")
        self.project = Project.objects.create(code="P001", name="Project One", domain="Corporate")
        self.department = Department.objects.create(code="D001", name="Operations")

    def builder_payload(self, question_id=None, question_text="Is the site clean?"):
        question = {
            "id": question_id or "tmp_question",
            "text": question_text,
            "type": "yes_no",
            "options": [],
            "required": True,
            "order": 1,
        }
        return {
            "sections": [
                {
                    "id": "tmp_section",
                    "title": "General",
                    "order": 1,
                    "collapsed": False,
                    "questions": [question],
                }
            ]
        }

    def post_builder(self, action="create", checklist=None, payload=None, **overrides):
        data = {
            "action": action,
            "checklist_pk": checklist.id if checklist else "",
            "checklist_id": checklist.checklist_id if checklist else "CL99",
            "name": overrides.pop("name", "Daily Safety Audit"),
            "checklist_type": str(self.checklist_type.id),
            "projects": [str(self.project.id)],
            "departments": [str(self.department.id)],
            "builder_state_json": json.dumps(payload or self.builder_payload()),
        }
        data.update(overrides)
        return self.client.post(
            reverse("admin_checklist_action"),
            data=data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_create_checklist_builder_uses_definition_models(self):
        response = self.post_builder()

        self.assertEqual(response.status_code, 200)
        checklist = ChecklistDefinition.objects.get(checklist_id="CL99")
        self.assertEqual(checklist.name, "Daily Safety Audit")
        self.assertEqual(checklist.checklist_type, self.checklist_type)
        self.assertEqual(list(checklist.projects.all()), [self.project])
        self.assertEqual(list(checklist.departments.all()), [self.department])
        question = checklist.questions.get()
        self.assertEqual(question.question_text, "Is the site clean?")
        self.assertEqual(question.type, ChecklistQuestion.TYPE_YES_NO)
        self.assertEqual(question.section, "General")
        self.assertTrue(question.required)
        self.assertFalse(Checklist.objects.exists())
        self.assertFalse(Section.objects.exists())
        self.assertFalse(Question.objects.exists())

    def test_edit_checklist_builder_updates_and_removes_questions(self):
        checklist = ChecklistDefinition.objects.create(
            checklist_id="CL10",
            name="Old Name",
            checklist_type=self.checklist_type,
        )
        stale_question = ChecklistQuestion.objects.create(
            checklist=checklist,
            question_text="Remove me",
            type=ChecklistQuestion.TYPE_SHORT_TEXT,
            section="Old",
            order=1,
        )
        kept_question = ChecklistQuestion.objects.create(
            checklist=checklist,
            question_text="Keep me",
            type=ChecklistQuestion.TYPE_SHORT_TEXT,
            section="Old",
            order=2,
        )
        payload = self.builder_payload(question_id=kept_question.id, question_text="Updated question")

        response = self.post_builder(action="edit", checklist=checklist, payload=payload, name="Updated Name")

        self.assertEqual(response.status_code, 200)
        checklist.refresh_from_db()
        self.assertEqual(checklist.name, "Updated Name")
        self.assertFalse(ChecklistQuestion.objects.filter(id=stale_question.id).exists())
        kept_question.refresh_from_db()
        self.assertEqual(kept_question.question_text, "Updated question")
        self.assertEqual(kept_question.type, ChecklistQuestion.TYPE_YES_NO)
        self.assertEqual(kept_question.section, "General")

    def test_option_based_questions_require_options(self):
        payload = self.builder_payload()
        payload["sections"][0]["questions"][0]["type"] = "dropdown"

        response = self.post_builder(payload=payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("requires at least one option", response.json()["errors"][0])
        self.assertFalse(ChecklistDefinition.objects.filter(checklist_id="CL99").exists())

    def test_admin_checklist_view_and_pdf_pages_render(self):
        checklist = ChecklistDefinition.objects.create(
            checklist_id="CL20",
            name="Printable Checklist",
            checklist_type=self.checklist_type,
        )
        ChecklistQuestion.objects.create(
            checklist=checklist,
            question_text="Print me",
            type=ChecklistQuestion.TYPE_SHORT_TEXT,
            section="Printable Section",
            order=1,
        )

        view_response = self.client.get(reverse("admin_checklist_view", args=[checklist.id]))
        pdf_response = self.client.get(reverse("admin_checklist_pdf", args=[checklist.id]))

        self.assertEqual(view_response.status_code, 200)
        self.assertContains(view_response, "Printable Checklist")
        self.assertContains(view_response, "Download PDF")
        self.assertContains(view_response, "Quality Control Management System")
        self.assertNotContains(view_response, "Open PDF View")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertEqual(
            pdf_response["Content-Disposition"],
            'attachment; filename="Printable_Checklist.pdf"',
        )
        self.assertTrue(pdf_response.content.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_response.content), 500)


class WorkflowPhase1Tests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="workflow_admin", password="pass12345")
        UserProfile.objects.create(user=self.admin_user, role="Admin")
        self.owner = User.objects.create_user(username="workflow_owner", password="pass12345")
        self.department = Department.objects.create(code="WF", name="Workflow")
        self.project = Project.objects.create(code="PWF", name="Workflow Project", domain="Corporate")
        UserProfile.objects.create(user=self.owner, role="User", department=self.department, project=self.project)
        self.checklist_type = ChecklistType.objects.create(name="Workflow Type")
        self.checklist = ChecklistDefinition.objects.create(
            checklist_id="CLWF",
            name="Workflow Checklist",
            checklist_type=self.checklist_type,
        )
        self.checklist.projects.add(self.project)
        self.checklist.departments.add(self.department)
        self.question = ChecklistQuestion.objects.create(
            checklist=self.checklist,
            question_text="Workflow answer",
            type=ChecklistQuestion.TYPE_SHORT_TEXT,
            section="Workflow",
            order=1,
        )

    def create_response(self, status):
        return ChecklistResponse.objects.create(
            checklist=self.checklist,
            submitted_by=self.owner,
            department=self.department,
            project=self.project,
            status=status,
        )

    def test_admin_dashboard_counts_pending_for_approval_and_wip(self):
        self.create_response(ResponseStatus.PENDING)
        self.create_response(ResponseStatus.PENDING_APPROVAL)
        self.create_response(ResponseStatus.WIP)
        self.create_response(ResponseStatus.APPROVED)
        self.create_response(ResponseStatus.REJECTED)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pending"], 2)
        self.assertEqual(response.context["pending_approval"], 1)
        self.assertEqual(response.context["legacy_pending"], 1)
        self.assertEqual(response.context["wip"], 1)
        chart_data = response.context["admin_dashboard_config"]["charts"]["submittedChecklists"]
        self.assertEqual(chart_data["pending"], 2)
        self.assertEqual(chart_data["pendingApproval"], 1)
        self.assertEqual(chart_data["legacyPending"], 1)
        self.assertEqual(chart_data["wip"], 1)

    def test_admin_response_table_hides_invalid_wip_actions(self):
        self.create_response(ResponseStatus.WIP)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_responses"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "WIP Drafts")
        self.assertContains(response, 'data-action="view"')
        self.assertContains(response, 'data-action="edit"')
        self.assertNotContains(response, 'data-action="approve"')
        self.assertNotContains(response, 'data-action="reject"')
        self.assertNotContains(response, 'data-action="toggle"')

    def test_legacy_pending_label_is_visible(self):
        self.create_response(ResponseStatus.PENDING)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_responses"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending (Legacy)")

    def test_rejected_response_owner_can_open_for_editing(self):
        rejected_response = self.create_response(ResponseStatus.REJECTED)
        ChecklistAnswer.objects.create(
            response=rejected_response,
            question=self.question,
            answer_text="Needs correction",
        )
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {"response_id": rejected_response.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Needs correction"')
        self.assertContains(response, f'value="{rejected_response.id}"')

    def test_response_submission_uses_user_assigned_hod(self):
        fallback_hod = User.objects.create_user(username="fallback_hod", password="pass12345")
        assigned_hod = User.objects.create_user(username="assigned_hod", password="pass12345")
        UserProfile.objects.create(user=fallback_hod, role="HOD", department=self.department)
        UserProfile.objects.create(user=assigned_hod, role="HOD", department=self.department)
        owner_profile = self.owner.userprofile
        owner_profile.assigned_hod = assigned_hod
        owner_profile.save(update_fields=["assigned_hod"])
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "submit",
                f"q_{self.question.id}": "Submitted answer",
            },
        )

        self.assertRedirects(response, reverse("my_submissions"))
        checklist_response = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertEqual(checklist_response.hod, assigned_hod)
        self.assertNotEqual(checklist_response.hod, fallback_hod)

    def test_only_assigned_hod_can_approve_response(self):
        assigned_hod = User.objects.create_user(username="approval_hod", password="pass12345")
        other_hod = User.objects.create_user(username="other_hod", password="pass12345")
        UserProfile.objects.create(user=assigned_hod, role="HOD", department=self.department)
        UserProfile.objects.create(user=other_hod, role="HOD", department=self.department)
        RolePermission.objects.create(role="HOD", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        response_obj.hod = assigned_hod
        response_obj.save(update_fields=["hod"])
        url = reverse("user_submission_action")

        self.client.force_login(other_hod)
        denied = self.client.post(url, {"action": "approve", "response_id": response_obj.id})
        self.assertEqual(denied.status_code, 403)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.PENDING_APPROVAL)

        self.client.force_login(assigned_hod)
        approved = self.client.post(url, {"action": "approve", "response_id": response_obj.id})
        self.assertEqual(approved.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.APPROVED)

    def test_management_can_override_any_response(self):
        management = User.objects.create_user(username="management_override", password="pass12345")
        UserProfile.objects.create(user=management, role="Management")
        RolePermission.objects.create(role="Management", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)

        self.client.force_login(management)
        result = self.client.post(
            reverse("user_submission_action"),
            {"action": "reject", "response_id": response_obj.id, "comment": "Management escalation"},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.REJECTED)
        decision = response_obj.decisions.get()
        self.assertEqual(decision.comment, "Management escalation")
        self.assertTrue(decision.is_override)

    def test_hod_rejection_requires_and_records_reason(self):
        assigned_hod = User.objects.create_user(username="rejecting_hod", password="pass12345")
        UserProfile.objects.create(user=assigned_hod, role="HOD", department=self.department)
        RolePermission.objects.create(role="HOD", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        response_obj.hod = assigned_hod
        response_obj.save(update_fields=["hod"])
        self.client.force_login(assigned_hod)

        result = self.client.post(
            reverse("user_submission_action"),
            {"action": "reject", "response_id": response_obj.id, "comment": "Evidence is incomplete."},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.REJECTED)
        decision = response_obj.decisions.get()
        self.assertEqual(decision.action, ResponseDecision.ACTION_REJECT)
        self.assertEqual(decision.comment, "Evidence is incomplete.")
        self.assertEqual(decision.actor, assigned_hod)
        self.assertFalse(decision.is_override)

    def test_hod_rejection_without_reason_fails(self):
        assigned_hod = User.objects.create_user(username="blank_reason_hod", password="pass12345")
        UserProfile.objects.create(user=assigned_hod, role="HOD", department=self.department)
        RolePermission.objects.create(role="HOD", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        response_obj.hod = assigned_hod
        response_obj.save(update_fields=["hod"])
        self.client.force_login(assigned_hod)

        result = self.client.post(
            reverse("user_submission_action"),
            {"action": "reject", "response_id": response_obj.id, "comment": "   "},
        )

        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json()["error"], "Rejection reason is required.")
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.PENDING_APPROVAL)
        self.assertFalse(response_obj.decisions.exists())

    def test_reject_without_reason_fails_model_validation(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)

        with self.assertRaises(ValidationError):
            ResponseDecision.objects.create(
                response=response_obj,
                action=ResponseDecision.ACTION_REJECT,
                comment="   ",
                actor=self.admin_user,
                actor_role="Admin",
                is_override=True,
            )

        self.assertFalse(response_obj.decisions.exists())

    def test_response_decision_cannot_be_modified_after_creation(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        decision = ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="Original comment",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )

        decision.comment = "Changed comment"
        with self.assertRaises(ValidationError):
            decision.save()
        with self.assertRaises(ValidationError):
            ResponseDecision.objects.filter(id=decision.id).update(comment="Bulk change")

        decision.refresh_from_db()
        self.assertEqual(decision.comment, "Original comment")

    def test_bulk_create_conflict_update_cannot_overwrite_decision(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        existing = ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="Original audit record",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )
        attempted_overwrite = ResponseDecision(
            id=existing.id,
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="Overwritten audit record",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )

        with self.assertRaises(ValidationError):
            ResponseDecision.objects.bulk_create(
                [attempted_overwrite],
                update_conflicts=True,
                update_fields=["comment"],
                unique_fields=["id"],
            )

        existing.refresh_from_db()
        self.assertEqual(existing.comment, "Original audit record")

        created = ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="New audit record",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )
        self.assertNotEqual(created.id, existing.id)
        self.assertEqual(ResponseDecision.objects.filter(response=response_obj).count(), 2)

    def test_response_decision_cannot_be_deleted_through_application_paths(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        decision = ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="Permanent history",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )

        with self.assertRaises(ValidationError):
            decision.delete()
        with self.assertRaises(ValidationError):
            ResponseDecision.objects.filter(id=decision.id).delete()

        self.client.force_login(self.admin_user)
        result = self.client.post(
            reverse("admin_response_action"),
            {"action": "delete", "response_id": response_obj.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(result.status_code, 400)
        self.assertTrue(ResponseDecision.objects.filter(id=decision.id).exists())
        self.assertTrue(ChecklistResponse.objects.filter(id=response_obj.id).exists())

    def test_response_decision_admin_is_read_only(self):
        model_admin = admin.site._registry[ResponseDecision]

        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))

    def test_hod_approval_records_optional_comment(self):
        assigned_hod = User.objects.create_user(username="commenting_hod", password="pass12345")
        UserProfile.objects.create(user=assigned_hod, role="HOD", department=self.department)
        RolePermission.objects.create(role="HOD", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        response_obj.hod = assigned_hod
        response_obj.save(update_fields=["hod"])
        self.client.force_login(assigned_hod)

        result = self.client.post(
            reverse("user_submission_action"),
            {"action": "approve", "response_id": response_obj.id, "comment": "Reviewed and complete."},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.APPROVED)
        decision = response_obj.decisions.get()
        self.assertEqual(decision.action, ResponseDecision.ACTION_APPROVE)
        self.assertEqual(decision.comment, "Reviewed and complete.")

    def test_admin_override_records_comment(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        self.client.force_login(self.admin_user)

        result = self.client.post(
            reverse("admin_response_action"),
            {"action": "approve", "response_id": response_obj.id, "comment": "Administrative override."},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.APPROVED)
        decision = response_obj.decisions.get()
        self.assertEqual(decision.comment, "Administrative override.")
        self.assertEqual(decision.actor_role, "Admin")
        self.assertTrue(decision.is_override)

    def test_owner_can_view_all_decision_comments(self):
        RolePermission.objects.create(role="User", visible_columns=["actions"], allowed_actions=[])
        response_obj = self.create_response(ResponseStatus.REJECTED)
        ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_REJECT,
            comment="Please correct the date.",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )
        ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            comment="Correction verified.",
            actor=self.admin_user,
            actor_role="Admin",
            is_override=True,
        )
        self.client.force_login(self.owner)

        result = self.client.get(
            reverse("user_submission_action"),
            {"action": "view", "response_id": response_obj.id},
        )

        self.assertEqual(result.status_code, 200)
        comments = [item["comment"] for item in result.json()["decisions"]]
        self.assertEqual(comments, ["Please correct the date.", "Correction verified."])

        page = self.client.get(reverse("my_submissions"))
        self.assertContains(page, 'data-action="view"')

    def test_toggle_action_is_removed_from_response_ui_and_backend(self):
        RolePermission.objects.create(
            role="Management",
            visible_columns=["actions"],
            allowed_actions=["view", "toggle"],
        )
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        self.client.force_login(self.admin_user)

        page = self.client.get(reverse("admin_responses"))
        action_result = self.client.post(
            reverse("admin_response_action"),
            {"action": "toggle", "response_id": response_obj.id},
        )

        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'data-action="toggle"')
        self.assertNotContains(page, '"toggle"')
        self.assertEqual(action_result.status_code, 403)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.PENDING_APPROVAL)

    def test_admin_response_table_labels_override_actions(self):
        self.create_response(ResponseStatus.PENDING_APPROVAL)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_responses"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Override Approve")
        self.assertContains(response, "Override Reject")


class SecurityHardeningTests(TestCase):
    def _pdf_upload(self, name="evidence.pdf"):
        buffer = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(buffer)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="application/pdf")

    def test_checklist_upload_rejects_html(self):
        uploaded = SimpleUploadedFile(
            "payload.html",
            b"<script>alert('xss')</script>",
            content_type="text/html",
        )

        with self.assertRaises(ValidationError):
            validate_checklist_upload(uploaded)

    def test_checklist_upload_rejects_spoofed_pdf(self):
        uploaded = SimpleUploadedFile(
            "payload.pdf",
            b"<script>alert('xss')</script>",
            content_type="application/pdf",
        )

        with self.assertRaises(ValidationError):
            validate_checklist_upload(uploaded)

    def test_checklist_upload_allows_pdf(self):
        uploaded = self._pdf_upload()

        validate_checklist_upload(uploaded)

    def test_checklist_upload_rejects_invalid_image(self):
        uploaded = SimpleUploadedFile(
            "payload.png",
            b"not a png image",
            content_type="image/png",
        )

        with self.assertRaises(ValidationError):
            validate_checklist_upload(uploaded)

    def test_checklist_upload_rejects_oversized_file(self):
        uploaded = SimpleUploadedFile(
            "large.txt",
            b"a" * (MAX_CHECKLIST_UPLOAD_SIZE + 1),
            content_type="text/plain",
        )

        with self.assertRaises(ValidationError):
            validate_checklist_upload(uploaded)

    def test_branding_upload_rejects_svg(self):
        uploaded = SimpleUploadedFile(
            "logo.svg",
            b"<svg><script>alert('xss')</script></svg>",
            content_type="image/svg+xml",
        )

        with self.assertRaises(ValidationError):
            validate_branding_upload(uploaded)

    def test_attachment_download_requires_response_scope(self):
        department = Department.objects.create(code="SEC", name="Security")
        project = Project.objects.create(code="PSEC", name="Project Security", domain="Corporate")
        checklist_type = ChecklistType.objects.create(name="Evidence")
        checklist = ChecklistDefinition.objects.create(
            checklist_id="CLSEC",
            name="Security Evidence",
            checklist_type=checklist_type,
        )
        checklist.projects.add(project)
        checklist.departments.add(department)
        question = ChecklistQuestion.objects.create(
            checklist=checklist,
            question_text="Upload evidence",
            type=ChecklistQuestion.TYPE_FILE_UPLOAD,
            section="Evidence",
            order=1,
        )
        owner = User.objects.create_user(username="owner", password="pass12345")
        other = User.objects.create_user(username="other", password="pass12345")
        admin = User.objects.create_user(username="admin_user", password="pass12345")
        UserProfile.objects.create(user=owner, role="User", department=department, project=project)
        UserProfile.objects.create(user=other, role="User")
        UserProfile.objects.create(user=admin, role="Admin")
        response = ChecklistResponse.objects.create(
            checklist=checklist,
            submitted_by=owner,
            department=department,
            project=project,
            status=ResponseStatus.PENDING_APPROVAL,
        )
        answer = ChecklistAnswer(response=response, question=question)
        answer.file.save(
            "evidence.txt",
            SimpleUploadedFile("evidence.txt", b"plain evidence", content_type="text/plain"),
            save=True,
        )
        url = reverse("checklist_answer_download", args=[answer.id])

        self.client.force_login(other)
        unauthorized = self.client.get(url)
        self.assertEqual(unauthorized.status_code, 404)

        self.client.force_login(owner)
        authorized = self.client.get(url)
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized["X-Content-Type-Options"], "nosniff")

        self.client.force_login(admin)
        admin_response = self.client.get(url)
        self.assertEqual(admin_response.status_code, 200)
