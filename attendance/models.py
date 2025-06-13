from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

# Create your models here.

class AttendanceRecord(models.Model):
    ATTENDANCE_STATUS_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
        ('no_attendance', 'No Attendance'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_hours = models.FloatField(default=0.0)
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='no_attendance'
    )

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.user.username} - {self.date}"

    def calculate_total_hours(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            self.total_hours = duration.total_seconds() / 3600

            if self.total_hours >= 8:
                self.attendance_status = 'full_day'
            elif self.total_hours >= 4:
                self.attendance_status = 'half_day'
            else:
                self.attendance_status = 'no_attendance'
        else:
            self.total_hours = 0.0
            self.attendance_status = 'no_attendance'

    def save(self, *args, **kwargs):
        self.calculate_total_hours()
        super().save(*args, **kwargs)
