from django.contrib import admin
from .models import AttendanceRecord

# Register your models here.

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'check_in_time', 'check_out_time', 'total_hours', 'attendance_status']
    list_filter = ['date', 'attendance_status']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['total_hours']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')