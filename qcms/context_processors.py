from django.conf import settings


def branding(request):
    return {
        'PROJECT_DISPLAY_NAME': getattr(settings, 'PROJECT_DISPLAY_NAME', 'QCMS - Quality Control Management System'),
        'PROJECT_SHORT_NAME': getattr(settings, 'PROJECT_SHORT_NAME', 'QCMS'),
    }
