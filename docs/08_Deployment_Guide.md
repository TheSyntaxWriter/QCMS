# Deployment Guide

## Current Deployment State

The current project settings are development-oriented. Before production deployment, create a production settings strategy and harden security settings.

The current configuration uses:

- `DEBUG=True`
- Hardcoded `SECRET_KEY`
- Empty `ALLOWED_HOSTS`
- SQLite database
- Local media storage
- Development media serving through Django URL patterns

These are not production-ready.

## Recommended Production Architecture

```text
Client Browser
  -> HTTPS reverse proxy such as Nginx/Caddy/IIS
  -> Gunicorn/uWSGI/Daphne running Django
  -> PostgreSQL database
  -> Static file storage/server
  -> Private or controlled media storage
```

On Windows deployments, use an equivalent production WSGI hosting strategy supported by the target environment.

## Environment Variables

Move sensitive and environment-specific settings out of source code.

Recommended variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DATABASE_URL` or individual database settings.
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_STATIC_ROOT`
- `DJANGO_MEDIA_ROOT`

## Security Settings

Production should set:

```python
DEBUG = False
ALLOWED_HOSTS = ["your-domain.example"]
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

Use HSTS only after confirming HTTPS is stable for the domain.

## Database

For production, prefer PostgreSQL over SQLite.

Recommended steps:

1. Provision PostgreSQL.
2. Configure Django database settings.
3. Run migrations:

```bash
python manage.py migrate
```

4. Create admin/superuser if needed:

```bash
python manage.py createsuperuser
```

5. Back up production database regularly.

## Static Files

Configure:

```python
STATIC_ROOT = BASE_DIR / "staticfiles"
```

Collect static files:

```bash
python manage.py collectstatic
```

Serve collected static files through the web server or a static file service.

## Media Files

Media files include:

- Profile images.
- Checklist answer uploads.
- Branding assets.

Production recommendations:

- Do not serve sensitive checklist uploads as unrestricted public files.
- Validate upload type and size.
- Store user uploads outside the application source tree where possible.
- Use authenticated download views for sensitive response attachments.
- Consider cloud/object storage if usage grows.

## Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Important runtime dependencies:

- Django.
- Pillow.
- WeasyPrint.
- PDF-related packages.
- Chart.js is currently loaded from CDN in templates.

WeasyPrint may require system libraries depending on OS and installation method.

## Migrations

Run migrations after deployment:

```bash
python manage.py migrate
```

Review migration history before production use because there are multiple checklist/status migrations and legacy models.

## Deployment Checks

Run:

```bash
python manage.py check --deploy
```

Resolve all warnings before exposing the app publicly.

## Logging

QCMS has application audit logging through `ActivityLog`, but production also needs infrastructure logging:

- Web server access logs.
- Web server error logs.
- Django application logs.
- Database logs.
- Backup/restore logs.

Recommended improvements:

- Configure Python logging in settings.
- Send errors to a monitoring system.
- Alert on repeated failed login attempts.

## Backups

Back up:

- Database.
- Media files.
- Environment configuration.
- Deployment scripts.

Backup frequency should reflect business recovery needs.

## Production Readiness Checklist

- `DEBUG=False`.
- Secret key loaded from environment.
- Hostnames configured.
- HTTPS enabled.
- Secure cookies enabled.
- HSTS enabled after HTTPS validation.
- Static files collected and served correctly.
- Media files served safely.
- Database moved from SQLite to PostgreSQL.
- Migrations applied.
- Admin user created.
- Upload validation hardened.
- XSS risks fixed in response detail modals.
- Rate limiting or lockout added to login.
- Backups configured.
- Monitoring/logging configured.
- `__pycache__`, local DB, and uploaded media removed from version control.

## Deployment Risks to Address

- Hardcoded development secret.
- Public media serving.
- Unrestricted checklist answer uploads.
- No login throttling.
- External CDN scripts without CSP/SRI.
- Mixed workflow statuses may confuse production reporting.
