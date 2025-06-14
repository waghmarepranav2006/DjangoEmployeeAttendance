from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import AttendanceRecord
import json


@login_required
def dashboard(request):
    today = timezone.now().date()

    # Get or create today's attendance record
    attendance_record, created = AttendanceRecord.objects.get_or_create(
        user=request.user,
        date=today,
        defaults={'check_in_time': None, 'check_out_time': None}
    )

    # Get filter parameter from request
    filter_type = request.GET.get('filter', 'all')

    # Base queryset
    attendance_queryset = AttendanceRecord.objects.filter(user=request.user)

    # Apply date filtering
    if filter_type == 'week':
        # Current week (Monday to Sunday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        attendance_history = attendance_queryset.filter(
            date__range=[start_of_week, end_of_week]
        )
    elif filter_type == 'month':
        # Current month
        attendance_history = attendance_queryset.filter(
            date__year=today.year,
            date__month=today.month
        )
    elif filter_type == 'year':
        # Current year
        attendance_history = attendance_queryset.filter(
            date__year=today.year
        )
    else:
        # All records (default)
        attendance_history = attendance_queryset

    # Order by date (latest first)
    attendance_history = attendance_history.order_by('-date', '-check_in_time')

    context = {
        'today_record': attendance_record,
        'attendance_history': attendance_history,
        'is_checked_in': attendance_record.check_in_time is not None and attendance_record.check_out_time is None,
    }

    return render(request, 'attendance/dashboard.html', context)


@login_required
@require_POST
@csrf_exempt
def check_in(request):
    today = timezone.now().date()

    try:
        attendance_record, created = AttendanceRecord.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'check_in_time': timezone.now()}
        )

        if not created and attendance_record.check_in_time is None:
            attendance_record.check_in_time = timezone.now()
            attendance_record.save()
        elif not created and attendance_record.check_in_time is not None:
            return JsonResponse({'success': False, 'message': 'Already checked in today'})

        return JsonResponse({
            'success': True,
            'message': 'Checked in successfully',
            'check_in_time': attendance_record.check_in_time.strftime('%H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
@csrf_exempt
def check_out(request):
    today = timezone.now().date()

    try:
        attendance_record = AttendanceRecord.objects.get(
            user=request.user,
            date=today
        )

        if attendance_record.check_in_time is None:
            return JsonResponse({'success': False, 'message': 'Please check in first'})

        if attendance_record.check_out_time is not None:
            return JsonResponse({'success': False, 'message': 'Already checked out today'})

        attendance_record.check_out_time = timezone.now()
        attendance_record.save()

        return JsonResponse({
            'success': True,
            'message': 'Checked out successfully',
            'check_out_time': attendance_record.check_out_time.strftime('%H:%M:%S'),
            'total_hours': round(attendance_record.total_hours, 2),
            'attendance_status': attendance_record.get_attendance_status_display()
        })
    except AttendanceRecord.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'No check-in record found for today'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def get_current_hours(request):
    today = timezone.now().date()

    try:
        attendance_record = AttendanceRecord.objects.get(
            user=request.user,
            date=today
        )

        if attendance_record.check_in_time and not attendance_record.check_out_time:
            current_time = timezone.now()
            duration = current_time - attendance_record.check_in_time
            current_hours = duration.total_seconds() / 3600

            return JsonResponse({
                'current_hours': round(current_hours, 2),
                'hours_for_half_day': max(0, 4 - current_hours),
                'hours_for_full_day': max(0, 8 - current_hours),
                'can_leave': current_hours >= 4
            })
        else:
            return JsonResponse({'current_hours': 0, 'can_leave': True})
    except AttendanceRecord.DoesNotExist:
        return JsonResponse({'current_hours': 0, 'can_leave': True})
