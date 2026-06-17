from django import template
from django.utils.html import format_html, format_html_join

from backend.icon_registry import DEFAULT_ICON_SLOTS, LUCIDE_ICON_REGISTRY, normalize_icon_slots, sanitize_icon_key


register = template.Library()


@register.simple_tag(takes_context=True)
def qcms_icon(context, slot_or_key, class_name='app-icon', label=''):
    icon_slots = normalize_icon_slots(context.get('GLOBAL_ICON_SLOTS'))
    icon_key = icon_slots.get(slot_or_key) or sanitize_icon_key(slot_or_key)
    icon = LUCIDE_ICON_REGISTRY[icon_key]
    paths = format_html_join('', '<path d="{}"></path>', ((path,) for path in icon['paths']))
    aria = format_html('aria-hidden="true"') if not label else format_html('role="img" aria-label="{}"', label)
    return format_html(
        '<svg class="{}" {} viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{}</svg>',
        class_name,
        aria,
        paths,
    )
