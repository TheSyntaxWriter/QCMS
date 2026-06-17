import base64
import json
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse
from pypdf import PdfWriter
from PIL import Image as PILImage

from .upload_validation import MAX_CHECKLIST_UPLOAD_SIZE, validate_branding_upload, validate_checklist_upload
from .models import (
    ActivityLog,
    AppSettings,
    Checklist,
    ChecklistAnswer,
    ChecklistDefinition,
    ChecklistQuestion,
    ChecklistResponse,
    ChecklistType,
    Department,
    Notification,
    NotificationSetting,
    Project,
    Question,
    ResponseDecision,
    RolePermission,
    Section,
    UserProfile,
)
from .workflow_service import ResponseStatus
from .notification_service import create_notifications


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


class AuthenticationAuditCoverageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auth_audit', password='pass12345')
        UserProfile.objects.create(user=self.user, role='User')

    def test_login_success_failure_and_logout_use_structured_event_keys(self):
        failed = self.client.post(reverse('login'), {'username': 'auth_audit', 'password': 'wrong'})
        self.assertEqual(failed.status_code, 200)
        self.assertTrue(ActivityLog.objects.filter(event_key='login.failed', target_id='auth_audit').exists())

        success = self.client.post(reverse('login'), {'username': 'auth_audit', 'password': 'pass12345'})
        self.assertEqual(success.status_code, 302)
        self.assertTrue(ActivityLog.objects.filter(event_key='login.success', target_id=str(self.user.id)).exists())

        self.client.get(reverse('logout'))
        self.assertTrue(ActivityLog.objects.filter(event_key='logout', target_id=str(self.user.id)).exists())


class TableFrameworkPhase0Tests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="table_admin", password="pass12345")
        UserProfile.objects.create(user=self.admin_user, role="Admin")
        self.owner = User.objects.create_user(username="table_owner", password="pass12345")
        self.department = Department.objects.create(code="TBL", name="Table Department")
        self.project = Project.objects.create(code="TBP", name="Table Project", domain="Corporate")
        UserProfile.objects.create(
            user=self.owner,
            role="User",
            department=self.department,
            project=self.project,
        )
        self.checklist_type = ChecklistType.objects.create(name="Table Type")

        for index in range(51):
            checklist = ChecklistDefinition.objects.create(
                checklist_id=f"CL-TBL-{index:02d}",
                name=f"Table Checklist {index:02d}",
                checklist_type=self.checklist_type,
            )
            checklist.departments.add(self.department)
            checklist.projects.add(self.project)
            ChecklistResponse.objects.create(
                checklist=checklist,
                submitted_by=self.owner,
                department=self.department,
                project=self.project,
                status=ResponseStatus.APPROVED,
            )
            ActivityLog.objects.create(
                user=self.owner,
                role="User",
                department=self.department,
                project=self.project,
                action_type="Table Test",
                module_name="Table Framework",
                description=f"Pagination record {index:02d}",
                status=ActivityLog.STATUS_INFO,
            )

    def assert_page_two_reachable(self, url_name, context_name, expected_pages, query=None):
        self.client.force_login(self.admin_user if url_name.startswith("admin_") else self.owner)
        query = query or {}
        first_page = self.client.get(reverse(url_name), query)
        second_page = self.client.get(reverse(url_name), {**query, "page": 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertContains(first_page, "Showing 1-")
        self.assertContains(first_page, f"of 51 results")
        self.assertContains(first_page, f"Page 1 of {expected_pages}")
        self.assertContains(first_page, "Go to next page")
        self.assertEqual(second_page.context[context_name].number, 2)
        self.assertContains(second_page, f"Page 2 of {expected_pages}")
        self.assertGreater(len(second_page.context[context_name].object_list), 0)

    def test_admin_checklists_page_two_is_reachable(self):
        self.assert_page_two_reachable("admin_checklists", "checklists", 3)

    def test_admin_responses_page_two_is_reachable_and_preserves_filters(self):
        self.client.force_login(self.admin_user)
        first_page = self.client.get(reverse("admin_responses"), {"status": ResponseStatus.APPROVED})

        self.assertContains(first_page, "?status=Approved&amp;page=2")
        self.assert_page_two_reachable(
            "admin_responses",
            "responses",
            3,
            {"status": ResponseStatus.APPROVED},
        )

    def test_activity_logs_page_two_is_reachable(self):
        self.assert_page_two_reachable("admin_logs", "logs", 3)

    def test_my_checklists_page_two_is_reachable(self):
        self.assert_page_two_reachable("my_checklists", "checklists", 3)

    def test_my_submissions_page_two_is_reachable(self):
        self.assert_page_two_reachable("my_submissions", "responses", 3)

    def test_empty_search_results_show_count_and_page_indicator(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin_checklists"), {"search": "no-such-checklist"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["checklists"].paginator.count, 0)
        self.assertContains(response, "Showing 0 of 0 results")
        self.assertContains(response, "Page 1 of 1")
        self.assertNotContains(response, "Go to next page")

    def test_page_size_selector_and_excel_export_use_complete_filtered_dataset(self):
        self.client.force_login(self.admin_user)
        page = self.client.get(reverse('admin_checklists'), {'page_size': 50})
        self.assertEqual(len(page.context['checklists'].object_list), 50)

        exported = self.client.get(reverse('admin_checklists'), {'search': 'CL-TBL-', 'export': 'xlsx'})
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(exported['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        with ZipFile(BytesIO(exported.content)) as workbook:
            sheet = workbook.read('xl/worksheets/sheet1.xml').decode('utf-8')
        self.assertIn('CL-TBL-00', sheet)
        self.assertIn('CL-TBL-50', sheet)

    def test_configured_default_page_size_is_used_and_query_override_wins(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.system_preferences = {
            **(settings_obj.system_preferences or {}),
            'table_default_page_size': 50,
            'table_density': 'compact',
        }
        settings_obj.save(update_fields=['system_preferences', 'updated_at'])
        self.client.force_login(self.admin_user)

        configured = self.client.get(reverse('admin_checklists'))
        overridden = self.client.get(reverse('admin_checklists'), {'page_size': 25})

        self.assertEqual(len(configured.context['checklists'].object_list), 50)
        self.assertEqual(configured.context['current_page_size'], 50)
        self.assertEqual(len(overridden.context['checklists'].object_list), 25)
        self.assertEqual(overridden.context['current_page_size'], 25)
        self.assertContains(configured, 'data-table-density="compact"')

    def test_excel_export_neutralizes_formula_injection(self):
        checklist = ChecklistDefinition.objects.get(checklist_id='CL-TBL-00')
        checklist.name = '=HYPERLINK("https://example.invalid")'
        checklist.save(update_fields=['name'])
        self.client.force_login(self.admin_user)

        exported = self.client.get(reverse('admin_checklists'), {'search': 'CL-TBL-00', 'export': 'xlsx'})
        with ZipFile(BytesIO(exported.content)) as workbook:
            sheet = workbook.read('xl/worksheets/sheet1.xml').decode('utf-8')
        self.assertIn("'=HYPERLINK", sheet)
        self.assertNotIn('<f>', sheet)


class ActivityLogIntegrityPhase0Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="audit_user", password="pass12345")
        UserProfile.objects.create(user=self.user, role="Admin")

    def create_log(self):
        return ActivityLog.objects.create(
            user=self.user,
            role="Admin",
            action_type="Integrity Test",
            module_name="Audit",
            description="ActivityLog append-only regression test.",
            status=ActivityLog.STATUS_SUCCESS,
        )

    def test_existing_log_creation_contract_remains_compatible(self):
        log = self.create_log()

        self.assertEqual(log.event_key, "")
        self.assertEqual(log.severity, ActivityLog.SEVERITY_MEDIUM)
        self.assertEqual(log.target_type, "")
        self.assertEqual(log.target_id, "")
        self.assertEqual(log.source, ActivityLog.SOURCE_UI)

    def test_activity_log_instance_cannot_be_modified_after_creation(self):
        log = self.create_log()
        log.description = "Edited description"

        with self.assertRaises(ValidationError):
            log.save()

        log.refresh_from_db()
        self.assertEqual(log.description, "ActivityLog append-only regression test.")

    def test_activity_log_queryset_update_is_blocked(self):
        log = self.create_log()

        with self.assertRaises(ValidationError):
            ActivityLog.objects.filter(pk=log.pk).update(description="Edited description")

        log.refresh_from_db()
        self.assertEqual(log.description, "ActivityLog append-only regression test.")

    def test_activity_log_instance_delete_is_blocked(self):
        log = self.create_log()

        with self.assertRaises(ValidationError):
            log.delete()

        self.assertTrue(ActivityLog.objects.filter(pk=log.pk).exists())

    def test_activity_log_queryset_delete_is_blocked(self):
        log = self.create_log()

        with self.assertRaises(ValidationError):
            ActivityLog.objects.filter(pk=log.pk).delete()

        self.assertTrue(ActivityLog.objects.filter(pk=log.pk).exists())

    def test_activity_log_bulk_update_is_blocked(self):
        log = self.create_log()
        log.description = "Bulk edited description"

        with self.assertRaises(ValidationError):
            ActivityLog.objects.bulk_update([log], ["description"])

        log.refresh_from_db()
        self.assertEqual(log.description, "ActivityLog append-only regression test.")

    def test_activity_log_normal_bulk_create_still_works(self):
        created = ActivityLog.objects.bulk_create([
            ActivityLog(
                user=self.user,
                role="Admin",
                action_type="Bulk Create One",
                module_name="Audit",
                description="First normal bulk-created activity log.",
                status=ActivityLog.STATUS_INFO,
            ),
            ActivityLog(
                user=self.user,
                role="Admin",
                action_type="Bulk Create Two",
                module_name="Audit",
                description="Second normal bulk-created activity log.",
                status=ActivityLog.STATUS_INFO,
            ),
        ])

        self.assertEqual(len(created), 2)
        self.assertEqual(ActivityLog.objects.filter(action_type__startswith="Bulk Create").count(), 2)

    def test_activity_log_bulk_create_conflict_update_is_blocked(self):
        log = self.create_log()

        with self.assertRaises(ValidationError):
            ActivityLog.objects.bulk_create(
                [
                    ActivityLog(
                        id=log.id,
                        user=self.user,
                        role="Admin",
                        action_type="Integrity Test",
                        module_name="Audit",
                        description="Conflict update attempted.",
                        status=ActivityLog.STATUS_FAILED,
                    )
                ],
                update_conflicts=True,
                update_fields=["description", "status"],
                unique_fields=["id"],
            )

        log.refresh_from_db()
        self.assertEqual(log.description, "ActivityLog append-only regression test.")
        self.assertEqual(log.status, ActivityLog.STATUS_SUCCESS)

    def test_activity_log_admin_is_read_only(self):
        admin_user = User.objects.create_superuser(
            username="audit_superuser",
            email="audit@example.com",
            password="pass12345",
        )
        request = RequestFactory().get("/admin/backend/activitylog/")
        request.user = admin_user
        model_admin = admin.site._registry[ActivityLog]

        self.assertFalse(model_admin.has_add_permission(request))
        self.assertFalse(model_admin.has_change_permission(request, self.create_log()))
        self.assertFalse(model_admin.has_delete_permission(request, self.create_log()))
        self.assertTrue(model_admin.has_view_permission(request))
        self.assertIn("event_key", model_admin.get_readonly_fields(request))
        self.assertIn("severity", model_admin.get_readonly_fields(request))


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

    def assert_response_activity_log(self, *, actor, response_obj, event_key, severity, source):
        log = ActivityLog.objects.get(
            user=actor,
            event_key=event_key,
            target_type="ChecklistResponse",
            target_id=str(response_obj.id),
        )
        self.assertEqual(log.module_name, "Response")
        self.assertEqual(log.status, ActivityLog.STATUS_SUCCESS)
        self.assertEqual(log.severity, severity)
        self.assertEqual(log.source, source)

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

    def test_geolocation_tracking_is_disabled_by_default_and_admin_can_enable_it(self):
        settings_obj = AppSettings.get_solo()
        self.assertFalse(settings_obj.security_settings.get("geolocation_tracking_enabled", False))
        self.client.force_login(self.admin_user)

        page = self.client.get(reverse("admin_control_panel"))
        result = self.client.post(
            reverse("admin_control_panel"),
            {
                "action": "save",
                "confirm_password": "pass12345",
                "web_app_name": "QCMS",
                "global_theme_color": "#0b1b68",
                "geolocation_tracking_enabled": "on",
            },
        )

        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Enable Geolocation Tracking")
        self.assertRedirects(result, reverse("admin_control_panel"))
        settings_obj.refresh_from_db()
        self.assertTrue(settings_obj.security_settings["geolocation_tracking_enabled"])
        self.assertTrue(ActivityLog.objects.filter(event_key='settings.control_panel_updated', target_type='AppSettings').exists())
        self.assertTrue(ActivityLog.objects.filter(event_key='geolocation_settings.updated', target_type='AppSettings').exists())

    def test_submit_captures_coordinates_accuracy_and_ip_when_enabled(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.security_settings = {"geolocation_tracking_enabled": True}
        settings_obj.save(update_fields=["security_settings", "updated_at"])
        self.client.force_login(self.owner)

        result = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "submit",
                f"q_{self.question.id}": "Located submission",
                "latitude": "19.076090",
                "longitude": "72.877426",
                "accuracy": "24.5",
            },
            REMOTE_ADDR="203.0.113.24",
        )

        self.assertRedirects(result, reverse("my_submissions"))
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertEqual(str(response_obj.latitude), "19.076090")
        self.assertEqual(str(response_obj.longitude), "72.877426")
        self.assertEqual(response_obj.accuracy, 24.5)
        self.assertEqual(response_obj.submission_ip, "203.0.113.24")

    def test_submit_succeeds_without_coordinates_when_permission_is_denied(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.security_settings = {"geolocation_tracking_enabled": True}
        settings_obj.save(update_fields=["security_settings", "updated_at"])
        self.client.force_login(self.owner)

        result = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "submit",
                f"q_{self.question.id}": "Permission denied submission",
            },
            REMOTE_ADDR="203.0.113.25",
        )

        self.assertRedirects(result, reverse("my_submissions"))
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertIsNone(response_obj.latitude)
        self.assertIsNone(response_obj.longitude)
        self.assertIsNone(response_obj.accuracy)
        self.assertEqual(response_obj.submission_ip, "203.0.113.25")

    def test_wip_never_captures_geolocation(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.security_settings = {"geolocation_tracking_enabled": True}
        settings_obj.save(update_fields=["security_settings", "updated_at"])
        self.client.force_login(self.owner)

        result = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "save_wip",
                f"q_{self.question.id}": "Draft answer",
                "latitude": "19.076090",
                "longitude": "72.877426",
                "accuracy": "10",
            },
            REMOTE_ADDR="203.0.113.26",
        )

        self.assertRedirects(result, reverse("my_submissions"))
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertEqual(response_obj.status, ResponseStatus.WIP)
        self.assertIsNone(response_obj.latitude)
        self.assertIsNone(response_obj.longitude)
        self.assertIsNone(response_obj.accuracy)
        self.assertIsNone(response_obj.submission_ip)

    def test_invalid_coordinates_are_not_stored(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.security_settings = {"geolocation_tracking_enabled": True}
        settings_obj.save(update_fields=["security_settings", "updated_at"])
        self.client.force_login(self.owner)

        result = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "submit",
                f"q_{self.question.id}": "Invalid coordinates",
                "latitude": "999",
                "longitude": "not-a-number",
                "accuracy": "-1",
            },
            REMOTE_ADDR="203.0.113.27",
        )

        self.assertRedirects(result, reverse("my_submissions"))
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertIsNone(response_obj.latitude)
        self.assertIsNone(response_obj.longitude)
        self.assertIsNone(response_obj.accuracy)
        self.assertEqual(response_obj.submission_ip, "203.0.113.27")

    def geolocation_response(self, **location):
        return ChecklistResponse(
            checklist=self.checklist,
            submitted_by=self.owner,
            project=self.project,
            department=self.department,
            status=ResponseStatus.PENDING_APPROVAL,
            **location,
        )

    def test_model_rejects_invalid_latitude(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(latitude=Decimal("90.000001")).save()

    def test_model_rejects_invalid_longitude(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(longitude=Decimal("-180.000001")).save()

    def test_model_rejects_negative_accuracy(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(accuracy=-0.1).save()

    def test_model_rejects_nan_latitude(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(latitude=Decimal("NaN")).save()

    def test_model_rejects_nan_longitude(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(longitude=Decimal("NaN")).save()

    def test_model_rejects_infinite_accuracy(self):
        with self.assertRaises(ValidationError):
            self.geolocation_response(accuracy=float("inf")).save()

    def test_model_accepts_valid_coordinates(self):
        response_obj = self.geolocation_response(
            latitude=Decimal("19.076090"),
            longitude=Decimal("72.877426"),
            accuracy=0,
        )

        response_obj.save()

        self.assertIsNotNone(response_obj.pk)

    def test_malformed_non_finite_submission_does_not_return_server_error(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.security_settings = {"geolocation_tracking_enabled": True}
        settings_obj.save(update_fields=["security_settings", "updated_at"])
        self.client.force_login(self.owner)

        result = self.client.post(
            reverse("user_checklist_fill", args=[self.checklist.id]),
            {
                "workflow_action": "submit",
                f"q_{self.question.id}": "Malformed location submission",
                "latitude": "NaN",
                "longitude": "NaN",
                "accuracy": "Infinity",
            },
            REMOTE_ADDR="203.0.113.29",
        )

        self.assertRedirects(result, reverse("my_submissions"))
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.assertIsNone(response_obj.latitude)
        self.assertIsNone(response_obj.longitude)
        self.assertIsNone(response_obj.accuracy)

    def test_queryset_update_cannot_bypass_geolocation_validation(self):
        response_obj = self.geolocation_response()
        response_obj.save()

        with self.assertRaises(ValidationError):
            ChecklistResponse.objects.filter(pk=response_obj.pk).update(latitude=Decimal("NaN"))

        response_obj.refresh_from_db()
        self.assertIsNone(response_obj.latitude)

    def test_location_is_visible_in_user_hod_and_admin_response_details(self):
        hod = User.objects.create_user(username="location_hod", password="pass12345")
        UserProfile.objects.create(user=hod, role="HOD", department=self.department)
        RolePermission.objects.create(role="HOD", visible_columns=["actions"], allowed_actions=["view"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        response_obj.hod = hod
        response_obj.latitude = "19.076090"
        response_obj.longitude = "72.877426"
        response_obj.accuracy = 15.0
        response_obj.submission_ip = "203.0.113.28"
        response_obj.save(update_fields=["hod", "latitude", "longitude", "accuracy", "submission_ip"])

        for user, url_name in (
            (self.owner, "user_submission_action"),
            (hod, "user_submission_action"),
            (self.admin_user, "admin_response_action"),
        ):
            self.client.force_login(user)
            result = self.client.get(
                reverse(url_name),
                {"action": "view", "response_id": response_obj.id},
            )
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["location"]["latitude"], 19.07609)
            self.assertEqual(result.json()["location"]["longitude"], 72.877426)
            self.assertEqual(result.json()["location"]["accuracy"], 15.0)
            self.assertEqual(result.json()["location"]["submission_ip"], "203.0.113.28")

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
        self.assert_response_activity_log(
            actor=assigned_hod,
            response_obj=response_obj,
            event_key="response.approved",
            severity=ActivityLog.SEVERITY_HIGH,
            source=ActivityLog.SOURCE_UI,
        )

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
        self.assert_response_activity_log(
            actor=management,
            response_obj=response_obj,
            event_key="response.override_rejected",
            severity=ActivityLog.SEVERITY_CRITICAL,
            source=ActivityLog.SOURCE_UI,
        )

    def test_management_override_approve_writes_activity_log_metadata(self):
        management = User.objects.create_user(username="management_override_approve", password="pass12345")
        UserProfile.objects.create(user=management, role="Management")
        RolePermission.objects.create(role="Management", visible_columns=["actions"], allowed_actions=["view", "approve", "reject"])
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)

        self.client.force_login(management)
        result = self.client.post(
            reverse("user_submission_action"),
            {"action": "approve", "response_id": response_obj.id, "comment": "Management approval override"},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.APPROVED)
        self.assert_response_activity_log(
            actor=management,
            response_obj=response_obj,
            event_key="response.override_approved",
            severity=ActivityLog.SEVERITY_CRITICAL,
            source=ActivityLog.SOURCE_UI,
        )

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
        self.assert_response_activity_log(
            actor=assigned_hod,
            response_obj=response_obj,
            event_key="response.rejected",
            severity=ActivityLog.SEVERITY_HIGH,
            source=ActivityLog.SOURCE_UI,
        )

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
        self.assert_response_activity_log(
            actor=self.admin_user,
            response_obj=response_obj,
            event_key="response.override_approved",
            severity=ActivityLog.SEVERITY_CRITICAL,
            source=ActivityLog.SOURCE_ADMIN,
        )

    def test_admin_override_reject_writes_activity_log_metadata(self):
        response_obj = self.create_response(ResponseStatus.PENDING_APPROVAL)
        self.client.force_login(self.admin_user)

        result = self.client.post(
            reverse("admin_response_action"),
            {"action": "reject", "response_id": response_obj.id, "comment": "Administrative rejection override."},
        )

        self.assertEqual(result.status_code, 200)
        response_obj.refresh_from_db()
        self.assertEqual(response_obj.status, ResponseStatus.REJECTED)
        self.assert_response_activity_log(
            actor=self.admin_user,
            response_obj=response_obj,
            event_key="response.override_rejected",
            severity=ActivityLog.SEVERITY_CRITICAL,
            source=ActivityLog.SOURCE_ADMIN,
        )

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
        self.assertTrue(ActivityLog.objects.filter(event_key='attachment.access_denied', target_id=str(answer.id)).exists())

        self.client.force_login(owner)
        authorized = self.client.get(url)
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized["X-Content-Type-Options"], "nosniff")
        self.assertTrue(ActivityLog.objects.filter(event_key='attachment.downloaded', target_id=str(answer.id)).exists())

        self.client.force_login(admin)
        admin_response = self.client.get(url)
        self.assertEqual(admin_response.status_code, 200)


class NotificationCenterTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(code='NTF', name='Notifications')
        self.project = Project.objects.create(code='N001', name='Notification Project', domain='Corporate')
        self.checklist_type = ChecklistType.objects.create(name='Notification Checklist')
        self.checklist = ChecklistDefinition.objects.create(
            checklist_id='CL-N1',
            name='Notification Workflow',
            checklist_type=self.checklist_type,
        )
        self.checklist.departments.add(self.department)
        self.checklist.projects.add(self.project)
        self.question = ChecklistQuestion.objects.create(
            checklist=self.checklist,
            question_text='Confirm completion',
            type=ChecklistQuestion.TYPE_SHORT_TEXT,
            required=True,
        )
        self.admin_user = User.objects.create_user(username='notification_admin', password='pass12345')
        self.management = User.objects.create_user(username='notification_management', password='pass12345')
        self.hod = User.objects.create_user(username='notification_hod', password='pass12345')
        self.owner = User.objects.create_user(username='notification_owner', password='pass12345')
        UserProfile.objects.create(user=self.admin_user, role='Admin')
        UserProfile.objects.create(user=self.management, role='Management')
        UserProfile.objects.create(user=self.hod, role='HOD', department=self.department, project=self.project)
        UserProfile.objects.create(
            user=self.owner,
            role='User',
            department=self.department,
            project=self.project,
            assigned_hod=self.hod,
        )
        RolePermission.objects.create(role='HOD', visible_columns=['actions'], allowed_actions=['view', 'approve', 'reject'])
        RolePermission.objects.create(role='Management', visible_columns=['actions'], allowed_actions=['view', 'approve', 'reject'])

    def submit_checklist(self, workflow_action='submit'):
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                reverse('user_checklist_fill', args=[self.checklist.id]),
                {
                    'workflow_action': workflow_action,
                    f'q_{self.question.id}': 'Complete',
                },
            )

    def test_notification_service_stores_required_fields_and_respects_priority(self):
        settings = NotificationSetting.get_solo()
        settings.event_settings = {
            'checklist_submitted': {'enabled': True, 'priority': 'High', 'popup': True},
        }
        settings.save()

        create_notifications(
            'checklist_submitted',
            self.owner,
            message='Checklist stored.',
            related_type='ChecklistResponse',
            related_id='42',
            related_url='/my-submissions/',
        )

        notification = Notification.objects.get(recipient=self.owner)
        self.assertEqual(notification.title, 'Checklist Submitted Successfully')
        self.assertEqual(notification.message, 'Checklist stored.')
        self.assertEqual(notification.priority, Notification.PRIORITY_HIGH)
        self.assertFalse(notification.is_read)
        self.assertEqual(notification.related_id, '42')

    def test_global_disable_prevents_notification_creation(self):
        settings = NotificationSetting.get_solo()
        settings.enable_notifications = False
        settings.save()

        create_notifications('checklist_submitted', self.owner, message='Should not exist.')

        self.assertFalse(Notification.objects.exists())

    def test_notification_api_is_recipient_scoped_and_supports_read_delete(self):
        first = create_notifications('checklist_submitted', self.owner, message='Owner only.')[0]
        create_notifications('checklist_submitted', self.hod, message='HOD only.')
        self.client.force_login(self.owner)

        listing = self.client.get(reverse('notification_list'))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual([item['id'] for item in listing.json()['notifications']], [first.id])

        marked = self.client.post(reverse('notification_mark_read', args=[first.id]))
        self.assertEqual(marked.status_code, 200)
        first.refresh_from_db()
        self.assertTrue(first.is_read)
        self.assertIsNotNone(first.read_at)

        deleted = self.client.post(reverse('notification_delete', args=[first.id]))
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(Notification.objects.filter(id=first.id).exists())

    def test_poll_returns_unread_count_and_only_default_high_popup(self):
        create_notifications('checklist_submitted', self.owner, message='Medium information.')
        high = create_notifications('checklist_rejected', self.owner, message='High action.', action_required=True)[0]
        self.client.force_login(self.owner)

        result = self.client.get(reverse('notification_poll'))

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['unread_count'], 2)
        self.assertEqual([item['id'] for item in result.json()['popups']], [high.id])
        high.refresh_from_db()
        self.assertIsNotNone(high.popup_shown_at)

    def test_submit_notifies_owner_and_assigned_hod_but_wip_does_not(self):
        wip_result = self.submit_checklist('save_wip')
        self.assertRedirects(wip_result, reverse('my_submissions'))
        self.assertFalse(Notification.objects.exists())

        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        self.client.force_login(self.owner)
        with self.captureOnCommitCallbacks(execute=True):
            submit_result = self.client.post(
                reverse('user_checklist_fill', args=[self.checklist.id]),
                {'workflow_action': 'submit', 'response_id': response_obj.id, f'q_{self.question.id}': 'Complete'},
            )

        self.assertRedirects(submit_result, reverse('my_submissions'))
        self.assertTrue(Notification.objects.filter(recipient=self.owner, event_key='checklist_submitted').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.hod, event_key='new_approval_request').exists())

    def test_hod_rejection_notifies_owner_and_exposes_comment_event(self):
        self.submit_checklist()
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        Notification.objects.all().delete()
        self.client.force_login(self.hod)

        with self.captureOnCommitCallbacks(execute=True):
            result = self.client.post(
                reverse('user_submission_action'),
                {'action': 'reject', 'response_id': response_obj.id, 'comment': 'Please correct the evidence.'},
            )

        self.assertEqual(result.status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=self.owner, event_key='checklist_rejected').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.owner, event_key='rejection_comment_available').exists())

    def test_management_override_creates_confirmation_and_owner_notification(self):
        self.submit_checklist()
        response_obj = ChecklistResponse.objects.get(submitted_by=self.owner)
        Notification.objects.all().delete()
        self.client.force_login(self.management)

        with self.captureOnCommitCallbacks(execute=True):
            result = self.client.post(
                reverse('user_submission_action'),
                {'action': 'approve', 'response_id': response_obj.id, 'comment': 'Oversight approval.'},
            )

        self.assertEqual(result.status_code, 200)
        self.assertTrue(Notification.objects.filter(recipient=self.owner, event_key='checklist_approved').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.management, event_key='override_approval_performed').exists())

    def test_missing_hod_submission_notifies_management_and_admin(self):
        profile = self.owner.userprofile
        profile.assigned_hod = None
        profile.save(update_fields=['assigned_hod'])

        self.submit_checklist()

        self.assertTrue(Notification.objects.filter(recipient=self.management, event_key='missing_assigned_hod_alert').exists())
        self.assertTrue(Notification.objects.filter(recipient=self.admin_user, event_key='missing_hod_assignment_detected').exists())

    def test_permission_denied_threshold_notifies_admin_once(self):
        self.client.force_login(self.owner)
        for _ in range(5):
            result = self.client.post(reverse('user_submission_action'), {'action': 'approve', 'response_id': '999'})
            self.assertEqual(result.status_code, 403)

        self.assertEqual(Notification.objects.filter(recipient=self.admin_user, event_key='permission_denied_threshold').count(), 1)
        self.assertEqual(ActivityLog.objects.filter(user=self.owner, event_key='permission.denied').count(), 5)

    def test_protected_audit_delete_notifies_admin(self):
        response_obj = ChecklistResponse.objects.create(
            checklist=self.checklist,
            submitted_by=self.owner,
            hod=self.hod,
            status=ResponseStatus.APPROVED,
        )
        ResponseDecision.objects.create(
            response=response_obj,
            action=ResponseDecision.ACTION_APPROVE,
            actor=self.hod,
            actor_role='HOD',
        )
        self.client.force_login(self.admin_user)

        with self.captureOnCommitCallbacks(execute=True):
            result = self.client.post(
                reverse('admin_response_action'),
                {'action': 'delete', 'response_id': response_obj.id},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            )

        self.assertEqual(result.status_code, 400)
        self.assertTrue(Notification.objects.filter(recipient=self.admin_user, event_key='protected_audit_action_blocked').exists())

    def test_notification_settings_page_is_admin_only_and_persists_events(self):
        self.client.force_login(self.owner)
        denied = self.client.get(reverse('admin_notification_settings'))
        self.assertRedirects(denied, reverse('home'), fetch_redirect_response=False)

        self.client.force_login(self.admin_user)
        result = self.client.post(reverse('admin_notification_settings'), {
            'enable_notifications': 'on',
            'enable_bell': 'on',
            'enable_popups': 'on',
            'retention_days': '180',
            'low_color': '#6B7280',
            'medium_color': '#2563EB',
            'high_color': '#EA580C',
            'critical_color': '#DC2626',
            'event_notification_settings_changed_enabled': 'on',
            'event_notification_settings_changed_priority': 'Critical',
            'event_notification_settings_changed_popup': 'on',
        })

        self.assertRedirects(result, reverse('admin_notification_settings'))
        settings = NotificationSetting.get_solo()
        self.assertEqual(settings.retention_days, 180)
        self.assertEqual(settings.event_settings['notification_settings_changed']['priority'], 'Critical')
        self.assertTrue(Notification.objects.filter(recipient=self.admin_user, event_key='notification_settings_changed').exists())
        self.assertTrue(ActivityLog.objects.filter(event_key='notification_settings.updated', target_type='NotificationSetting').exists())

    def test_authenticated_header_contains_notification_bell(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('my_checklists'))
        self.assertContains(response, 'id="notificationBell"')
        self.assertContains(response, 'class="qcms-avatar qcms-avatar--header"')
        self.assertContains(response, 'class="qcms-avatar__initials"')
        self.assertContains(response, 'Open profile for notification_owner')

    def test_admin_ui_uses_notification_control_name(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_notification_settings'))
        self.assertNotContains(response, '<span class="app-sidebar__label">Notification Control</span>', html=True)
        self.assertContains(response, 'aria-label="Control Panel sections"')
        self.assertContains(response, '<div>Notification Control</div>', html=True)
        self.assertContains(response, 'Control Panel section')
        self.assertContains(response, reverse('admin_control_panel') + '#components')
        self.assertContains(response, 'Save Notification Control Settings')


class ControlPanel2Phase1Tests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username='control_admin', password='pass12345')
        UserProfile.objects.create(user=self.admin_user, role='Admin')
        self.client.force_login(self.admin_user)

    def test_control_panel_contains_all_phase_one_sections(self):
        response = self.client.get(reverse('admin_control_panel'))

        self.assertEqual(response.status_code, 200)
        for section_id in (
            'general', 'branding', 'appearance', 'components', 'header-navigation',
            'icon-gallery', 'tables', 'notification-control', 'security', 'operations',
        ):
            self.assertContains(response, f'id="{section_id}"')
        self.assertContains(response, 'Corporate Minimal')
        self.assertContains(response, 'Modern Enterprise')
        self.assertContains(response, 'Premium Executive')
        self.assertContains(response, reverse('admin_notification_settings'))
        self.assertContains(response, 'Icon Gallery')
        self.assertContains(response, 'icon_slot_dashboard')

    def test_component_header_and_table_settings_persist_and_are_audited(self):
        response = self.client.post(reverse('admin_control_panel'), {
            'action': 'save',
            'confirm_password': 'pass12345',
            'web_app_name': 'QCMS Enterprise',
            'global_theme_color': '#2457A6',
            'font_family': 'Inter',
            'card_profile': 'premium',
            'button_profile': 'corporate',
            'cursor_profile': 'modern',
            'header_settings_present': '1',
            'header_show_welcome_text': 'on',
            'header_density': 'compact',
            'icon_gallery_present': '1',
            'icon_slot_dashboard': 'file-check-2',
            'icon_slot_control': 'shield-check',
            'table_default_page_size': '50',
            'table_density': 'spacious',
        })

        self.assertRedirects(response, reverse('admin_control_panel'))
        settings_obj = AppSettings.get_solo()
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.theme_settings['card_profile'], 'premium')
        self.assertEqual(settings_obj.theme_settings['button_profile'], 'corporate')
        self.assertEqual(settings_obj.theme_settings['cursor_profile'], 'modern')
        self.assertEqual(settings_obj.theme_settings['icon_slots']['dashboard'], 'file-check-2')
        self.assertEqual(settings_obj.theme_settings['icon_slots']['control'], 'shield-check')
        self.assertFalse(settings_obj.theme_settings['header_show_avatar'])
        self.assertTrue(settings_obj.theme_settings['header_show_welcome_text'])
        self.assertEqual(settings_obj.theme_settings['header_density'], 'compact')
        self.assertEqual(settings_obj.system_preferences['table_default_page_size'], 50)
        self.assertEqual(settings_obj.system_preferences['table_density'], 'spacious')
        for event_key in (
            'settings.control_panel_updated', 'settings.theme_updated',
            'settings.header_updated', 'settings.icon_gallery_updated', 'settings.table_updated',
        ):
            self.assertTrue(ActivityLog.objects.filter(event_key=event_key, target_type='AppSettings').exists())

    def test_root_attributes_and_header_visibility_use_normalized_settings(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.theme_settings = {
            'global_theme_color': '#0b1b68',
            'font_family': 'Inter',
            'card_profile': 'corporate',
            'button_profile': 'premium',
            'cursor_profile': 'modern',
            'header_show_avatar': False,
            'header_show_welcome_text': False,
            'header_density': 'compact',
        }
        settings_obj.system_preferences = {'table_default_page_size': 25, 'table_density': 'compact'}
        settings_obj.save(update_fields=['theme_settings', 'system_preferences', 'updated_at'])

        response = self.client.get(reverse('admin_dashboard'))

        self.assertContains(response, 'data-card-profile="corporate"')
        self.assertContains(response, 'data-button-profile="premium"')
        self.assertContains(response, 'data-cursor-profile="modern"')
        self.assertContains(response, 'data-header-density="compact"')
        self.assertContains(response, 'data-table-density="compact"')
        self.assertNotContains(response, 'class="topbar-identity"')
        self.assertNotContains(response, 'class="topbar-welcome-text"')

    def test_invalid_profile_values_fall_back_to_safe_defaults(self):
        response = self.client.post(reverse('admin_control_panel'), {
            'action': 'save',
            'confirm_password': 'pass12345',
            'web_app_name': 'QCMS',
            'global_theme_color': 'not-a-color',
            'font_family': 'Untrusted Font',
            'card_profile': 'unknown',
            'button_profile': 'unknown',
            'cursor_profile': 'unknown',
            'header_settings_present': '1',
            'header_show_avatar': 'on',
            'header_show_welcome_text': 'on',
            'header_density': 'unknown',
            'icon_gallery_present': '1',
            'icon_slot_dashboard': '<svg/onload=alert(1)>',
            'table_default_page_size': '999',
            'table_density': 'unknown',
        })

        self.assertRedirects(response, reverse('admin_control_panel'))
        settings_obj = AppSettings.get_solo()
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.theme_settings['global_theme_color'], '#0b1b68')
        self.assertEqual(settings_obj.theme_settings['font_family'], 'Inter')
        self.assertEqual(settings_obj.theme_settings['card_profile'], 'modern')
        self.assertEqual(settings_obj.theme_settings['button_profile'], 'modern')
        self.assertEqual(settings_obj.theme_settings['cursor_profile'], 'classic')
        self.assertEqual(settings_obj.theme_settings['header_density'], 'comfortable')
        self.assertEqual(settings_obj.theme_settings['icon_slots']['dashboard'], 'layout-dashboard')
        self.assertEqual(settings_obj.system_preferences['table_default_page_size'], 25)
        self.assertEqual(settings_obj.system_preferences['table_density'], 'comfortable')

    def test_sidebar_uses_allowlisted_icon_registry(self):
        settings_obj = AppSettings.get_solo()
        settings_obj.theme_settings = {
            'global_theme_color': '#0b1b68',
            'font_family': 'Inter',
            'icon_slots': {'dashboard': 'file-check-2', 'control': 'shield-check'},
        }
        settings_obj.save(update_fields=['theme_settings', 'updated_at'])

        response = self.client.get(reverse('admin_dashboard'))

        self.assertContains(response, '<svg class="app-icon"')
        self.assertContains(response, '<svg class="app-icon app-icon--chevron"')
        self.assertContains(response, '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"></path>', html=True)
        self.assertNotContains(response, 'app-icon--dashboard')


class HeaderIdentityStandardizationTests(TestCase):
    def create_role_user(self, username, role, first_name, last_name):
        user = User.objects.create_user(
            username=username,
            password='pass12345',
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.create(user=user, role=role)
        return user

    def test_admin_header_always_uses_full_name_not_module_context(self):
        admin_user = self.create_role_user('identity_admin', 'Admin', 'Anika', 'Admin')
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin_control_panel'))

        self.assertContains(response, '<span class="topbar-welcome-text">Welcome, Anika Admin</span>', html=True)
        self.assertNotContains(response, '<span class="topbar-welcome-text">Enterprise Configuration</span>', html=True)
        self.assertContains(response, '<div>Control Panel</div>', html=True)

    def test_user_hod_and_management_headers_use_full_name(self):
        for role in ('User', 'HOD', 'Management'):
            with self.subTest(role=role):
                user = self.create_role_user(f'identity_{role.lower()}', role, role, 'Member')
                self.client.force_login(user)

                response = self.client.get(reverse('my_checklists'))

                self.assertContains(response, f'<span class="topbar-welcome-text">Welcome, {role} Member</span>', html=True)
                self.client.logout()


class AvatarRenderingTests(TestCase):
    def create_profile(self, username, role, *, first_name='', last_name='', image_name=''):
        user = User.objects.create_user(
            username=username,
            password='pass12345',
            first_name=first_name,
            last_name=last_name,
        )
        profile = UserProfile.objects.create(user=user, role=role)
        if image_name:
            profile.profile_image.name = image_name
            profile.save(update_fields=['profile_image'])
        return user

    def test_user_header_with_image_uses_shared_circular_avatar(self):
        user = self.create_profile('user_image', 'User', image_name='profile_images/user-image.jpg')
        self.client.force_login(user)

        response = self.client.get(reverse('my_checklists'))

        self.assertContains(response, 'class="qcms-avatar qcms-avatar--header"')
        self.assertContains(response, 'class="qcms-avatar__image"')
        self.assertContains(response, '/media/profile_images/user-image.jpg')

    def test_user_header_without_image_uses_initials_fallback(self):
        user = self.create_profile('user_fallback', 'User', first_name='Uma', last_name='Rao')
        self.client.force_login(user)

        response = self.client.get(reverse('my_checklists'))

        self.assertContains(response, 'class="qcms-avatar__initials"')
        self.assertContains(response, 'aria-label="Uma Rao initials"')

    def test_admin_with_image_uses_shared_avatar_in_header_and_profile(self):
        admin_user = self.create_profile('admin_image', 'Admin', image_name='profile_images/admin-image.jpg')
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin_profile'))

        self.assertContains(response, 'class="qcms-avatar qcms-avatar--header"')
        self.assertContains(response, 'class="qcms-avatar qcms-avatar--profile"')
        self.assertContains(response, '/media/profile_images/admin-image.jpg', count=2)
        self.assertContains(response, 'id="avatarPreview"')

    def test_admin_without_image_uses_same_initials_fallback_on_both_surfaces(self):
        admin_user = self.create_profile('admin_fallback', 'Admin', first_name='Asha', last_name='Nair')
        self.client.force_login(admin_user)

        response = self.client.get(reverse('admin_profile'))

        self.assertContains(response, 'class="qcms-avatar qcms-avatar--header"')
        self.assertContains(response, 'class="qcms-avatar qcms-avatar--profile"')
        self.assertContains(response, 'aria-label="Asha Nair initials"', count=2)

    def test_hod_and_management_headers_use_shared_avatar_component(self):
        for role in ('HOD', 'Management'):
            with self.subTest(role=role):
                user = self.create_profile(f'{role.lower()}_avatar', role, first_name=role, last_name='User')
                self.client.force_login(user)
                response = self.client.get(reverse('my_checklists'))
                self.assertContains(response, 'class="qcms-avatar qcms-avatar--header"')
                self.assertContains(response, f'aria-label="{role} User initials"')
                self.client.logout()

    def test_profile_pages_use_shared_modern_enterprise_content_and_cropper(self):
        for role, url_name in (('Admin', 'admin_profile'), ('User', 'user_profile')):
            with self.subTest(role=role):
                user = self.create_profile(f'{role.lower()}_modern', role, first_name=role, last_name='Profile')
                self.client.force_login(user)
                response = self.client.get(reverse(url_name))
                self.assertContains(response, 'class="profile-identity"')
                self.assertContains(response, 'class="profile-content-grid"')
                self.assertContains(response, 'id="cropModal" role="dialog" aria-modal="true"')
                self.assertContains(response, 'id="zoomOutButton"')
                self.assertContains(response, 'id="zoomInButton"')
                self.assertContains(response, 'id="resetCropButton"')
                self.assertContains(response, 'id="cancelCropButton"')
                self.assertContains(response, 'id="applyCropButton"')
                self.assertContains(response, '/static/shared/profile.css')
                self.assertContains(response, '/static/shared/profile.js')
                self.client.logout()

    def test_cropper_assets_include_viewport_layout_and_safe_enhancement(self):
        static_root = Path(settings.BASE_DIR) / 'frontend' / 'static' / 'shared'
        crop_css = (static_root / 'profile.css').read_text(encoding='utf-8')
        crop_script = (static_root / 'profile.js').read_text(encoding='utf-8')

        self.assertIn('grid-template-rows:auto minmax(0,1fr) auto auto', crop_css)
        self.assertIn('height:min(760px,calc(100dvh', crop_css)
        self.assertIn('max-height:100%', crop_css)
        self.assertIn('min-height:100dvh', crop_css)
        self.assertIn('@media(max-height:560px)', crop_css)
        self.assertIn('.profile-crop-dialog__header p{display:none}', crop_css)
        self.assertIn("imageOrientation: 'from-image'", crop_script)
        self.assertIn("status.textContent = 'Optimizing photo...'", crop_script)
        self.assertIn('sourceUrl = await enhancedImageUrl(file)', crop_script)
        self.assertIn('function correctedLevels', crop_script)
        self.assertIn('function enhancePixels', crop_script)
        self.assertIn('const amount = .12', crop_script)

    def test_profile_upload_normalizes_square_image_and_removes_replaced_file(self):
        user = self.create_profile('normalized_avatar', 'User', first_name='Nora', last_name='Square')
        profile = user.userprofile
        source = BytesIO()
        PILImage.new('RGB', (900, 450), (210, 120, 60)).save(source, format='PNG')
        data_url = 'data:image/png;base64,' + base64.b64encode(source.getvalue()).decode('ascii')

        storage_settings = {
            'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
            'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
        }
        with self.settings(STORAGES=storage_settings):
            old_image = BytesIO()
            PILImage.new('RGB', (32, 32), (20, 30, 40)).save(old_image, format='JPEG')
            profile.profile_image.save(
                'previous-avatar.jpg',
                SimpleUploadedFile('previous-avatar.jpg', old_image.getvalue(), content_type='image/jpeg'),
                save=True,
            )
            previous_name = profile.profile_image.name
            storage = profile.profile_image.storage
            self.assertTrue(storage.exists(previous_name))
            self.client.force_login(user)

            response = self.client.post(reverse('user_profile'), {
                'action': 'update_image',
                'cropped_image': data_url,
            })

            self.assertRedirects(response, reverse('user_profile'))
            profile.refresh_from_db()
            self.assertFalse(storage.exists(previous_name))
            profile.profile_image.open('rb')
            with PILImage.open(profile.profile_image.file) as saved:
                self.assertEqual(saved.size, (512, 512))
                self.assertEqual(saved.format, 'JPEG')
                corner = saved.convert('RGB').getpixel((0, 0))
                self.assertGreater(sum(corner), 100)
