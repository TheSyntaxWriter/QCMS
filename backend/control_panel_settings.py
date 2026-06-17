import re

from .icon_registry import DEFAULT_ICON_SLOTS, normalize_icon_slots, sanitize_icon_key


CARD_PROFILES = (
    ('corporate', 'Corporate Minimal'),
    ('modern', 'Modern Enterprise'),
    ('premium', 'Premium Executive'),
)
BUTTON_PROFILES = (
    ('corporate', 'Corporate'),
    ('modern', 'Modern'),
    ('premium', 'Premium'),
)
CURSOR_PROFILES = (
    ('classic', 'Classic Enterprise'),
    ('modern', 'Modern SaaS'),
    ('premium', 'Premium Interactive'),
)
HEADER_DENSITIES = (
    ('comfortable', 'Comfortable'),
    ('compact', 'Compact'),
)
TABLE_DENSITIES = (
    ('compact', 'Compact'),
    ('comfortable', 'Comfortable'),
    ('spacious', 'Spacious'),
)
PAGE_SIZE_OPTIONS = (25, 50, 100, 250)
FONT_OPTIONS = ('Inter', 'Poppins', 'Roboto', 'Open Sans', 'Nunito Sans', 'Source Sans Pro')

DEFAULT_THEME_SETTINGS = {
    'mode': 'light',
    'global_theme_color': '#0b1b68',
    'primary_color': '#0b1b68',
    'sidebar_color': '#0b1b68',
    'header_color': '#0b1b68',
    'button_style': 'rounded',
    'font_family': 'Inter',
    'layout_width': 'boxed',
    'card_profile': 'modern',
    'button_profile': 'modern',
    'cursor_profile': 'classic',
    'header_show_avatar': True,
    'header_show_welcome_text': True,
    'header_density': 'comfortable',
    'icon_slots': DEFAULT_ICON_SLOTS.copy(),
}

DEFAULT_SYSTEM_PREFERENCES = {
    'timezone': 'UTC',
    'date_format': 'YYYY-MM-DD',
    'table_default_page_size': 25,
    'table_density': 'comfortable',
}

HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


def _choice(value, choices, fallback):
    allowed = {choice[0] for choice in choices}
    return value if value in allowed else fallback


def normalize_theme_settings(value=None):
    source = value if isinstance(value, dict) else {}
    result = {**DEFAULT_THEME_SETTINGS, **source}
    color = result.get('global_theme_color') or result.get('primary_color') or DEFAULT_THEME_SETTINGS['global_theme_color']
    if not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
        color = DEFAULT_THEME_SETTINGS['global_theme_color']
    result.update({
        'global_theme_color': color,
        'primary_color': color,
        'sidebar_color': color,
        'header_color': color,
        'font_family': result.get('font_family') if result.get('font_family') in FONT_OPTIONS else 'Inter',
        'card_profile': _choice(result.get('card_profile'), CARD_PROFILES, 'modern'),
        'button_profile': _choice(result.get('button_profile'), BUTTON_PROFILES, 'modern'),
        'cursor_profile': _choice(result.get('cursor_profile'), CURSOR_PROFILES, 'classic'),
        'header_show_avatar': bool(result.get('header_show_avatar', True)),
        'header_show_welcome_text': bool(result.get('header_show_welcome_text', True)),
        'header_density': _choice(result.get('header_density'), HEADER_DENSITIES, 'comfortable'),
        'icon_slots': normalize_icon_slots(result.get('icon_slots')),
    })
    return result


def normalize_system_preferences(value=None):
    source = value if isinstance(value, dict) else {}
    result = {**DEFAULT_SYSTEM_PREFERENCES, **source}
    try:
        page_size = int(result.get('table_default_page_size', 25))
    except (TypeError, ValueError):
        page_size = 25
    result['table_default_page_size'] = page_size if page_size in PAGE_SIZE_OPTIONS else 25
    result['table_density'] = _choice(result.get('table_density'), TABLE_DENSITIES, 'comfortable')
    return result


def posted_theme_settings(post, current=None):
    result = normalize_theme_settings(current)
    for key in ('global_theme_color', 'font_family', 'card_profile', 'button_profile', 'cursor_profile', 'header_density'):
        if key in post:
            result[key] = (post.get(key) or '').strip()
    if post.get('header_settings_present') == '1':
        result['header_show_avatar'] = post.get('header_show_avatar') == 'on'
        result['header_show_welcome_text'] = post.get('header_show_welcome_text') == 'on'
    if post.get('icon_gallery_present') == '1':
        icon_slots = normalize_icon_slots(result.get('icon_slots'))
        if post.get('icon_gallery_reset') == '1':
            icon_slots = DEFAULT_ICON_SLOTS.copy()
        else:
            for slot, default_icon in DEFAULT_ICON_SLOTS.items():
                field_name = f'icon_slot_{slot}'
                if field_name in post:
                    icon_slots[slot] = sanitize_icon_key((post.get(field_name) or '').strip(), default_icon)
        result['icon_slots'] = icon_slots
    return normalize_theme_settings(result)


def posted_system_preferences(post, current=None):
    result = normalize_system_preferences(current)
    if 'table_default_page_size' in post:
        result['table_default_page_size'] = post.get('table_default_page_size')
    if 'table_density' in post:
        result['table_density'] = post.get('table_density')
    return normalize_system_preferences(result)
