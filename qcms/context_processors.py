from django.conf import settings
from backend.models import AppSettings
from backend.control_panel_settings import normalize_system_preferences, normalize_theme_settings


def branding(request):
    app_settings = AppSettings.get_solo()
    theme = normalize_theme_settings(app_settings.theme_settings)
    system_preferences = normalize_system_preferences(app_settings.system_preferences)
    return {
        'PROJECT_DISPLAY_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_DISPLAY_NAME', 'QCMS'),
        'PROJECT_SHORT_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_SHORT_NAME', 'QCMS'),
        'GLOBAL_BRANDING': app_settings,
        'GLOBAL_THEME': theme,
        'GLOBAL_SYSTEM_PREFERENCES': system_preferences,
    }
