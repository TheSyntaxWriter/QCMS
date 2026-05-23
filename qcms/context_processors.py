from django.conf import settings
from backend.models import AppSettings


def branding(request):
    app_settings = AppSettings.get_solo()
    theme = app_settings.theme_settings or {}
    return {
        'PROJECT_DISPLAY_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_DISPLAY_NAME', 'QCMS - Quality Control Management System'),
        'PROJECT_SHORT_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_SHORT_NAME', 'QCMS'),
        'GLOBAL_BRANDING': app_settings,
        'GLOBAL_THEME': theme,
    }
