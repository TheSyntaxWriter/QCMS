# Database Design

## Overview

The database is managed by Django ORM models in `backend/models.py`. The configured database is SQLite for the current local project. The schema supports user profiles, organizational scoping, checklist templates, checklist questions, submitted responses, answers, permissions, activity logs, and application settings.

## Entity Relationship Summary

```text
Django User
  1 -> 1 UserProfile
  1 -> many ChecklistResponse as submitted_by
  1 -> many ChecklistResponse as hod
  1 -> many ChecklistResponse as updated_by
  1 -> many ActivityLog

Department
  1 -> many UserProfile
  many <-> many ChecklistDefinition
  1 -> many ChecklistResponse
  1 -> many ActivityLog

Project
  1 -> many UserProfile
  many <-> many ChecklistDefinition
  1 -> many ChecklistResponse
  1 -> many ActivityLog

ChecklistType
  1 -> many ChecklistDefinition

ChecklistDefinition
  1 -> many ChecklistQuestion
  1 -> many ChecklistResponse
  many <-> many Project
  many <-> many Department

ChecklistQuestion
  1 -> many ChecklistAnswer

ChecklistResponse
  1 -> many ChecklistAnswer

RolePermission
  per role permission configuration

AppSettings
  singleton-style row with pk=1
```

## Models

### Project

Represents a project/business unit.

Fields:

- `code`: unique project code.
- `name`: display name.
- `domain`: `Corporate` or `Non-Corporate`.
- `is_active`: active/inactive switch.
- `created_at`, `updated_at`: timestamps.

Relationships:

- Referenced by `UserProfile.project`.
- Referenced by `ChecklistDefinition.projects`.
- Referenced by `ChecklistResponse.project`.
- Referenced by `ActivityLog.project`.

### Department

Represents an organizational department.

Fields:

- `code`: unique department code.
- `name`: display name.
- `is_active`: active/inactive switch.
- `created_at`, `updated_at`: timestamps.

Relationships:

- Referenced by `UserProfile.department`.
- Referenced by `ChecklistDefinition.departments`.
- Referenced by `ChecklistResponse.department`.
- Referenced by `ActivityLog.department`.

### UserProfile

Extends Django's built-in `User` with QCMS-specific metadata.

Fields:

- `user`: one-to-one link to Django `User`.
- `role`: `User`, `HOD`, `Management`, or `Admin`.
- `department`: optional department.
- `project`: optional project.
- `is_active`: profile-level active switch.
- `employee_id`: optional employee identifier.
- `phone_number`: optional validated phone number.
- `profile_image`: optional profile image upload.
- `created_at`: timestamp.

Relationships:

- One profile belongs to one `User`.
- Department and project determine checklist visibility and response scope.

### ChecklistType

Checklist category/type master.

Fields:

- `name`: unique type name.
- `is_active`: active/inactive switch.
- `created_at`, `updated_at`: timestamps.

Relationships:

- Referenced by `ChecklistDefinition.checklist_type`.

### ChecklistDefinition

The active checklist template/header model.

Fields:

- `checklist_id`: unique code, indexed.
- `name`: checklist name.
- `checklist_type`: protected foreign key to `ChecklistType`.
- `projects`: many-to-many eligible projects.
- `departments`: many-to-many eligible departments.
- `is_active`: active/inactive switch.
- `created_at`, `updated_at`: timestamps.

Meta:

- Default ordering: newest updated first.

Relationships:

- Has many `ChecklistQuestion` rows.
- Has many `ChecklistResponse` rows.
- Assigned to many projects and departments.

### ChecklistQuestion

Question inside a checklist definition.

Question types:

- `short_text`
- `long_text`
- `multiple_choice`
- `checkbox`
- `dropdown`
- `file_upload`
- `yes_no`
- `date`

Fields:

- `checklist`: parent `ChecklistDefinition`.
- `question_text`: question label/body.
- `type`: selected question type.
- `options`: JSON list for multiple choice, checkbox, and dropdown.
- `order`: display order.
- `section`: section title stored as text.
- `required`: whether answer is required on final submit.
- `created_at`, `updated_at`: timestamps.

Meta:

- Default ordering: `order`, then `id`.

Relationships:

- Has many `ChecklistAnswer` rows.

### ChecklistResponse

A user's checklist response instance.

Fields:

- `checklist`: parent checklist definition.
- `submitted_by`: user who created/submitted the response.
- `project`: project captured from submitter profile.
- `department`: department captured from submitter profile.
- `hod`: HOD user resolved from department.
- `status`: workflow status.
- `submitted_at`: creation timestamp.
- `updated_at`: update timestamp.
- `updated_by`: last user who changed the response.

Indexes:

- `status`
- `submitted_at`
- `project`
- `submitted_by`

Relationships:

- Has many `ChecklistAnswer` rows.
- Reviewed by HOD/Management/Admin depending on role and scope.

### ChecklistAnswer

Answer to one question within one response.

Fields:

- `response`: parent checklist response.
- `question`: answered checklist question.
- `answer_text`: text answer or pipe-delimited checkbox values.
- `file`: optional uploaded file for file upload questions.
- `created_at`, `updated_at`: timestamps.

Upload path:

```text
checklist_uploads/<checklist_id>_q<question_id>_u<user_id>_<ddmmyyyy>.<ext>
```

### Legacy Checklist, Section, Question

These models represent an older checklist structure:

- `Checklist`
- `Section`
- `Question`

The active builder tests assert that new checklist creation uses `ChecklistDefinition` and `ChecklistQuestion`, not these legacy models.

### RolePermission

Stores configurable response table permissions by role.

Fields:

- `role`: unique role. Choices: `User`, `HOD`, `Management`.
- `visible_columns`: JSON list of visible response table columns.
- `selected_projects`: JSON list, currently stored for configuration.
- `allowed_actions`: JSON list of actions.
- `updated_at`: timestamp.

Note: Admin permissions are hardcoded as full access in the permission service.

### ActivityLog

Audit log model for user/system actions.

Fields:

- `user`: optional user.
- `role`: user's role at the time.
- `department`: user's department at the time.
- `project`: user's project at the time.
- `action_type`: action label.
- `module_name`: module/category.
- `description`: human-readable event description.
- `ip_address`: request IP.
- `user_agent`: request user agent.
- `status`: `Success`, `Failed`, or `Info`.
- `old_data`, `new_data`: optional JSON snapshots.
- `timestamp`: log time.

Indexes:

- `module_name`, `action_type`
- `user`, `timestamp`
- `department`, `project`, `timestamp`

### AppSettings

Singleton-style global application settings.

Fields:

- `web_app_name`
- `logo`
- `favicon`
- `sidebar_logo`
- `general_settings`
- `theme_settings`
- `system_preferences`
- `security_settings`
- `notification_settings`
- `updated_at`

Access pattern:

- `AppSettings.get_solo()` gets or creates row `pk=1`.

## Key Design Notes

- Many-to-many tables generated by Django support checklist assignment to multiple projects and departments.
- Response data denormalizes project/department from the submitter profile at submission time.
- Question sections are stored as text on `ChecklistQuestion`, not as a separate active section table.
- Checkbox answers are stored as a pipe-delimited string in `answer_text`.
- File upload answers are stored in the media filesystem with a database file path.

## Recommended Database Improvements

- Add a uniqueness constraint on `ChecklistAnswer(response, question)`.
- Add composite indexes for common response filters, such as `(status, submitted_at)`, `(project, status, submitted_at)`, `(department, status, submitted_at)`, and `(submitted_by, status, submitted_at)`.
- Decide whether `Pending` and `Pending for Approval` are both needed; simplify the status model.
- Remove or archive legacy `Checklist`, `Section`, and `Question` models after confirming no production data depends on them.
- Normalize checklist sections into a first-class model if section-level metadata grows.
- Consider storing checkbox answers as JSON instead of pipe-delimited text.
- Move from SQLite to PostgreSQL or another production database for concurrent multi-user deployments.
