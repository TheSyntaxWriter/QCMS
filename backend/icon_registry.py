ICON_CATEGORIES = (
    ('navigation', 'Navigation'),
    ('workflow', 'Workflow'),
    ('people', 'People'),
    ('operations', 'Operations'),
    ('security', 'Security'),
)


LUCIDE_ICON_REGISTRY = {
    'layout-dashboard': {
        'label': 'Dashboard',
        'category': 'navigation',
        'paths': ('M3 13h8V3H3v10Z', 'M13 21h8V11h-8v10Z', 'M3 21h8v-6H3v6Z', 'M13 9h8V3h-8v6Z'),
    },
    'list-checks': {
        'label': 'Checklist',
        'category': 'workflow',
        'paths': ('M3 6h1', 'M3 12h1', 'M3 18h1', 'M8 6h13', 'M8 12h13', 'M8 18h13'),
    },
    'file-check-2': {
        'label': 'Approved File',
        'category': 'workflow',
        'paths': ('M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z', 'M14 2v6h6', 'm9 15 2 2 4-4'),
    },
    'message-square-text': {
        'label': 'Response',
        'category': 'workflow',
        'paths': ('M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', 'M8 8h8', 'M8 12h6'),
    },
    'users': {
        'label': 'Users',
        'category': 'people',
        'paths': ('M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'),
    },
    'circle-user-round': {
        'label': 'Profile',
        'category': 'people',
        'paths': ('M18 20a6 6 0 0 0-12 0', 'M12 14a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z'),
    },
    'building-2': {
        'label': 'Department',
        'category': 'operations',
        'paths': ('M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18', 'M6 12H4a2 2 0 0 0-2 2v8', 'M18 9h2a2 2 0 0 1 2 2v11', 'M10 6h4', 'M10 10h4', 'M10 14h4', 'M10 18h4'),
    },
    'folder-kanban': {
        'label': 'Project',
        'category': 'operations',
        'paths': ('M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.5L10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2Z', 'M8 12h3', 'M13 12h3', 'M8 16h5'),
    },
    'settings': {
        'label': 'Control Panel',
        'category': 'operations',
        'paths': ('M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.73l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'),
    },
    'scroll-text': {
        'label': 'Logs',
        'category': 'operations',
        'paths': ('M8 21h12a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2H8', 'M16 17H6a2 2 0 1 1 0-4h10', 'M16 13H6a2 2 0 1 1 0-4h10', 'M16 9H6a2 2 0 1 1 0-4h10'),
    },
    'bell': {
        'label': 'Notification Control',
        'category': 'operations',
        'paths': ('M10.268 21a2 2 0 0 0 3.464 0', 'M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.674C19.41 13.956 18 12.499 18 8a6 6 0 0 0-12 0c0 4.499-1.411 5.956-2.738 7.326Z'),
    },
    'shield-check': {
        'label': 'Security',
        'category': 'security',
        'paths': ('M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67 0C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z', 'm9 12 2 2 4-4'),
    },
    'log-out': {
        'label': 'Logout',
        'category': 'navigation',
        'paths': ('M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4', 'm16 17 5-5-5-5', 'M21 12H9'),
    },
    'chevron-right': {
        'label': 'Chevron',
        'category': 'navigation',
        'paths': ('m9 18 6-6-6-6',),
    },
}


DEFAULT_ICON_SLOTS = {
    'dashboard': 'layout-dashboard',
    'checklist': 'list-checks',
    'response': 'message-square-text',
    'user': 'users',
    'department': 'building-2',
    'project': 'folder-kanban',
    'control': 'settings',
    'logs': 'scroll-text',
    'profile': 'circle-user-round',
    'logout': 'log-out',
    'chevron': 'chevron-right',
    'notification': 'bell',
    'security': 'shield-check',
}


ICON_SLOT_LABELS = {
    'dashboard': 'Dashboard',
    'checklist': 'Checklist',
    'response': 'Response',
    'user': 'Users',
    'department': 'Departments',
    'project': 'Projects',
    'control': 'Control Panel',
    'logs': 'Activity Logs',
    'profile': 'Profile',
    'logout': 'Logout',
    'notification': 'Notification Control',
    'security': 'Security',
}


def sanitize_icon_key(value, fallback='layout-dashboard'):
    key = value if isinstance(value, str) else ''
    return key if key in LUCIDE_ICON_REGISTRY else fallback


def normalize_icon_slots(value=None):
    source = value if isinstance(value, dict) else {}
    normalized = {}
    for slot, default_icon in DEFAULT_ICON_SLOTS.items():
        normalized[slot] = sanitize_icon_key(source.get(slot), default_icon)
    return normalized


def icon_options_for_template():
    return [
        {
            'key': key,
            'label': config['label'],
            'category': config['category'],
        }
        for key, config in sorted(LUCIDE_ICON_REGISTRY.items(), key=lambda item: item[1]['label'])
    ]


def icon_slots_for_template(slots=None):
    normalized = normalize_icon_slots(slots)
    return [
        {
            'slot': slot,
            'label': ICON_SLOT_LABELS.get(slot, slot.replace('_', ' ').title()),
            'selected': normalized[slot],
            'default': DEFAULT_ICON_SLOTS[slot],
        }
        for slot in DEFAULT_ICON_SLOTS
    ]
