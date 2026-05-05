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
