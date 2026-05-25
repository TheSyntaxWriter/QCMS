from django.conf import settings
from backend.models import AppSettings


def branding(request):
    app_settings = AppSettings.get_solo()
    theme = app_settings.theme_settings or {}
    theme_color = theme.get('global_theme_color') or theme.get('primary_color') or '#0b1b68'
    return {
        'PROJECT_DISPLAY_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_DISPLAY_NAME', 'QCMS'),
        'PROJECT_SHORT_NAME': app_settings.web_app_name or getattr(settings, 'PROJECT_SHORT_NAME', 'QCMS'),
        'GLOBAL_BRANDING': app_settings,
        'GLOBAL_THEME': {**theme, 'global_theme_color': theme_color, 'primary_color': theme_color, 'sidebar_color': theme_color, 'header_color': theme_color},
    }
