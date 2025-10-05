from django.contrib import admin
from .models import UserProfile, Department, Subject, Meeting, Note, Attendance

admin.site.register(UserProfile)
admin.site.register(Department)
admin.site.register(Subject)
admin.site.register(Meeting)
admin.site.register(Note)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'meeting', 'join_time', 'leave_time', 'duration', 'present')
    readonly_fields = ('duration', )
