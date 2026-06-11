from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Department)
admin.site.register(UserProfile)
admin.site.register(ChecklistType)
admin.site.register(ChecklistDefinition)
admin.site.register(ChecklistQuestion)
admin.site.register(ChecklistResponse)
admin.site.register(ChecklistAnswer)
admin.site.register(RolePermission)
admin.site.register(Notification)


@admin.register(ResponseDecision)
class ResponseDecisionAdmin(admin.ModelAdmin):
    list_display = ('response', 'action', 'actor', 'actor_role', 'is_override', 'created_at')
    readonly_fields = ('response', 'action', 'comment', 'actor', 'actor_role', 'is_override', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
