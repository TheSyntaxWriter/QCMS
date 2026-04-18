from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile
from .models import Department, Project, Checklist


class AccessControlTests(TestCase):
    def create_user_with_role(self, username, role):
        user = User.objects.create_user(username=username, password="pass12345")
        UserProfile.objects.create(user=user, role=role)
        return user

    def test_admin_pages_require_login(self):
        admin_urls = [
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
            "admin_departments",
            "admin_projects",
            "admin_checklists",
            "admin_responses",
            "admin_create",
        ]

        for url_name in admin_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(response, reverse("home"))

    def test_admin_pages_allow_admin_users(self):
        user = self.create_user_with_role("admin_user", "Admin")
        self.client.force_login(user)

        admin_urls = [
            "admin_departments",
            "admin_projects",
            "admin_checklists",
            "admin_responses",
            "admin_create",
        ]

        for url_name in admin_urls:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_management_dashboard_access_control(self):
        response = self.client.get(reverse("management_dashboard"))
        self.assertRedirects(response, reverse("login"))

        user = self.create_user_with_role("hod_user", "HOD")
        self.client.force_login(user)
        response = self.client.get(reverse("management_dashboard"))
        self.assertRedirects(response, reverse("home"))

        management_user = self.create_user_with_role("mgmt_user", "Management")
        self.client.force_login(management_user)
        response = self.client.get(reverse("management_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_edit_delete_department(self):
        admin = self.create_user_with_role("dept_admin", "Admin")
        self.client.force_login(admin)

        create_response = self.client.post(reverse("admin_departments"), {
            "action": "create",
            "code": "DEP-100",
            "name": "Department A",
            "is_active": "on",
        })
        self.assertRedirects(create_response, reverse("admin_departments"))
        department = Department.objects.get(code="DEP-100")
        self.assertEqual(department.name, "Department A")

        update_response = self.client.post(reverse("admin_departments"), {
            "action": "update",
            "department_id": department.id,
            "code": "DEP-100",
            "name": "Department A Updated",
        })
        self.assertRedirects(update_response, reverse("admin_departments"))
        department.refresh_from_db()
        self.assertEqual(department.name, "Department A Updated")
        self.assertFalse(department.is_active)

        delete_response = self.client.post(reverse("admin_departments"), {
            "action": "delete",
            "department_id": department.id,
        })
        self.assertRedirects(delete_response, reverse("admin_departments"))
        self.assertFalse(Department.objects.filter(id=department.id).exists())

    def test_admin_can_create_edit_delete_project(self):
        admin = self.create_user_with_role("project_admin", "Admin")
        self.client.force_login(admin)

        create_response = self.client.post(reverse("admin_projects"), {
            "action": "create",
            "code": "PRJ-100",
            "name": "Project Alpha",
            "domain": "Corporate",
            "is_active": "on",
        })
        self.assertRedirects(create_response, reverse("admin_projects"))
        project = Project.objects.get(code="PRJ-100")
        self.assertEqual(project.name, "Project Alpha")

        update_response = self.client.post(reverse("admin_projects"), {
            "action": "update",
            "project_id": project.id,
            "code": "PRJ-100",
            "name": "Project Alpha Updated",
            "domain": "Non-Corporate",
        })
        self.assertRedirects(update_response, reverse("admin_projects"))
        project.refresh_from_db()
        self.assertEqual(project.name, "Project Alpha Updated")
        self.assertEqual(project.domain, "Non-Corporate")
        self.assertFalse(project.is_active)

        delete_response = self.client.post(reverse("admin_projects"), {
            "action": "delete",
            "project_id": project.id,
        })
        self.assertRedirects(delete_response, reverse("admin_projects"))
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_admin_can_create_edit_delete_checklist(self):
        admin = self.create_user_with_role("checklist_admin", "Admin")
        self.client.force_login(admin)

        department = Department.objects.create(code="DEP-CHK", name="Checklist Dept")
        project = Project.objects.create(code="PRJ-CHK", name="Checklist Project", domain="Corporate")

        create_response = self.client.post(reverse("admin_checklists"), {
            "action": "create",
            "code": "CHK-100",
            "name": "Daily Safety",
            "checklist_type": "Daily",
            "department_id": department.id,
            "project_id": project.id,
            "is_active": "on",
        })
        self.assertRedirects(create_response, reverse("admin_checklists"))
        checklist = Checklist.objects.get(code="CHK-100")
        self.assertEqual(checklist.name, "Daily Safety")

        update_response = self.client.post(reverse("admin_checklists"), {
            "action": "update",
            "checklist_id": checklist.id,
            "code": "CHK-100",
            "name": "Daily Safety Updated",
            "checklist_type": "Weekly",
            "department_id": department.id,
            "project_id": project.id,
        })
        self.assertRedirects(update_response, reverse("admin_checklists"))
        checklist.refresh_from_db()
        self.assertEqual(checklist.name, "Daily Safety Updated")
        self.assertEqual(checklist.checklist_type, "Weekly")
        self.assertFalse(checklist.is_active)

        delete_response = self.client.post(reverse("admin_checklists"), {
            "action": "delete",
            "checklist_id": checklist.id,
        })
        self.assertRedirects(delete_response, reverse("admin_checklists"))
        self.assertFalse(Checklist.objects.filter(id=checklist.id).exists())
