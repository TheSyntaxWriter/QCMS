from django.contrib import admin
from .models import *

admin.site.register(Project)
admin.site.register(Department)
admin.site.register(UserProfile)
admin.site.register(Checklist)
admin.site.register(Question)
admin.site.register(ChecklistTransaction)
admin.site.register(Answer)