import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .workflow_service import ResponseStatus

from .models import (
    Checklist,
    ChecklistDefinition,
    ChecklistQuestion,
    ChecklistResponse,
    ChecklistType,
    Department,
    Project,
    Question,
    RolePermission,
    Section,
    UserProfile,
)


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
                self.assertRedirects(response, reverse("my_checklists"))

    def test_dashboard_access_control(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("login"))

        user = self.create_user_with_role("hod_user", "HOD")
        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("hod_reviews"))

        management_user = self.create_user_with_role("mgmt_user", "Management")
        self.client.force_login(management_user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)

        legacy_response = self.client.get(reverse("management_dashboard"))
        self.assertRedirects(legacy_response, reverse("dashboard"))

    def test_home_redirects_by_role(self):
        role_expected = {
            'User': 'my_checklists',
            'HOD': 'hod_reviews',
            'Management': 'dashboard',
            'Admin': 'admin_dashboard',
        }
        for role, expected in role_expected.items():
            user = self.create_user_with_role(f'{role.lower()}_user', role)
            self.client.force_login(user)
            response = self.client.get(reverse('home'))
            self.assertRedirects(response, reverse(expected))
            self.client.logout()

    def test_hod_review_queue_shows_pending_approval_and_allows_approval(self):
        department = Department.objects.create(code="D-HOD", name="HOD Department")
        project = Project.objects.create(code="P-HOD", name="HOD Project", domain="Ops")
        hod_user = User.objects.create_user(username="hod_reviewer", password="pass12345")
        UserProfile.objects.create(user=hod_user, role="HOD", department=department, project=project)
        submitter = User.objects.create_user(username="submitter", password="pass12345")
        checklist_type = ChecklistType.objects.create(name="Review Type")
        checklist = ChecklistDefinition.objects.create(
            checklist_id="CL-HOD",
            name="HOD Reviewed Checklist",
            checklist_type=checklist_type,
        )
        response_obj = ChecklistResponse.objects.create(
            checklist=checklist,
            submitted_by=submitter,
            project=project,
            department=department,
            hod=hod_user,
            status=ResponseStatus.PENDING_APPROVAL,
        )
        RolePermission.objects.create(
            role="HOD",
            visible_columns=["checklist_id", "checklist_name", "submitted_by", "status", "actions"],
            allowed_actions=["view", "approve", "reject"],
        )

        self.client.force_login(hod_user)
        queue_response = self.client.get(reverse("hod_reviews"))

        self.assertEqual(queue_response.status_code, 200)
        self.assertContains(queue_response, "HOD Review Queue")
        self.assertContains(queue_response, "CL-HOD")
        self.assertContains(queue_response, "Approve")
        self.assertContains(queue_response, "Reject")

        approve_response = self.client.post(
            reverse("user_submission_action"),
            data={"action": "approve", "response_id": response_obj.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(approve_response.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.APPROVED)



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
        self.assertContains(view_response, "Work Management System")
        self.assertNotContains(view_response, "Open PDF View")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertEqual(
            pdf_response["Content-Disposition"],
            'attachment; filename="Printable_Checklist.pdf"',
        )
        self.assertTrue(pdf_response.content.startswith(b"%PDF-"))
        self.assertGreater(len(pdf_response.content), 500)
