from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from attendance.models import AttendanceRecord
from django.utils import timezone
from datetime import datetime, timedelta, time
import random


class Command(BaseCommand):
    help = 'Create dummy attendance data for demo purposes'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to generate data for')
        parser.add_argument('--username', type=str, help='Username to create data for')

    def handle(self, *args, **options):
        days = options['days']
        username = options.get('username')

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
                return
        else:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in the system'))
                return

        created_count = 0

        for i in range(days):
            date = timezone.now().date() - timedelta(days=i + 1)

            # Skip weekends
            if date.weekday() >= 5:
                continue

            # Check if record already exists
            if AttendanceRecord.objects.filter(user=user, date=date).exists():
                continue

            # Generate realistic work patterns
            patterns = [
                # Full day workers
                {'min_hours': 8, 'max_hours': 9, 'check_in_start': 8, 'check_in_end': 9},
                # Early birds
                {'min_hours': 8.5, 'max_hours': 9.5, 'check_in_start': 7, 'check_in_end': 8},
                # Late starters
                {'min_hours': 7.5, 'max_hours': 8.5, 'check_in_start': 9, 'check_in_end': 10},
                # Half day (occasionally)
                {'min_hours': 4, 'max_hours': 5, 'check_in_start': 8, 'check_in_end': 9},
            ]

            # Choose pattern (90% full day, 10% half day)
            if random.random() < 0.9:
                pattern = random.choice(patterns[:3])  # Full day patterns
            else:
                pattern = patterns[3]  # Half day pattern

            # Generate times
            check_in_hour = random.randint(pattern['check_in_start'], pattern['check_in_end'])
            check_in_minute = random.randint(0, 59)
            check_in_time = timezone.make_aware(datetime.combine(date, time(check_in_hour, check_in_minute)))

            work_hours = random.uniform(pattern['min_hours'], pattern['max_hours'])
            check_out_time = check_in_time + timedelta(hours=work_hours)

            # Create record
            AttendanceRecord.objects.create(
                user=user,
                date=date,
                check_in_time=check_in_time,
                check_out_time=check_out_time,
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} attendance records for {user.username}')
        )