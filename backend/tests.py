import json
from io import BytesIO

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
