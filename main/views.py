from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.http import HttpResponseNotFound, HttpResponse
from django.urls import reverse
from django.utils.text import slugify
import csv

from .models import (
    Meeting, Attendance, Note, Subject, UserProfile, Department, Notification
)
from .forms import NoteForm, MeetingForm, ProfileForm


from .models import Department, UserProfile

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        department_id = request.POST.get('department')

        # Username uniqueness check
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return redirect('register')

        # Password matching check
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        # Department selected check
        if not department_id:
            messages.error(request, 'Please select a department.')
            return redirect('register')

        # Create user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        # Assign department in user profile
        department = Department.objects.get(id=department_id)
        UserProfile.objects.create(user=user, department=department, role='student')

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    else:
        departments = Department.objects.all()
        return render(request, 'main/register.html', {'departments': departments})



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            if hasattr(user, 'userprofile'):
                if user.userprofile.role == 'student':
                    return redirect('student_dashboard')
                elif user.userprofile.role == 'faculty':
                    return redirect('faculty_dashboard')
                elif user.userprofile.role == 'admin':
                    return redirect('admin_dashboard')
            return redirect('index')
        else:
            return render(request, 'main/login.html', {'error': 'Invalid credentials'})
    return render(request, 'main/login.html')




def index(request):
    return render(request, 'main/index.html')


from django.utils import timezone
from datetime import datetime, time







from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from .models import Department, Subject, Meeting, Note

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.utils import timezone
from .models import Department, Subject, Meeting, Note

@login_required
def faculty_dashboard(request):
    print('Dashboard view called for user:', request.user)
    try:
        user_profile = request.user.userprofile
        department = user_profile.department
    except AttributeError:
        department = None

    try:
        if isinstance(department, str):
            department_obj = Department.objects.get(name=department)
        else:
            department_obj = department
    except ObjectDoesNotExist:
        department_obj = None

    if department_obj:
        subjects = Subject.objects.filter(department=department_obj, faculty=request.user)
    else:
        subjects = Subject.objects.none()

    # Get ALL meetings (past and future), order with newest first
    meetings = Meeting.objects.filter(subject__faculty=request.user).order_by('-schedule_datetime')

    notes = Note.objects.filter(subject__faculty=request.user).order_by('-created_at')

    avg_attendance = 0  # Placeholder for any attendance calculation

    current_time = timezone.now()  # pass current time for template logic

    context = {
        'subjects': subjects,
        'meetings': meetings,
        'notes': notes,
        'avg_attendance': avg_attendance,
        'section': 'dashboard',
        'current_time': current_time,
    }

    return render(request, 'main/faculty_dashboard.html', context)





@login_required
def create_meeting(request):
    if request.user.userprofile.role != 'faculty':
        messages.error(request, 'Unauthorized access.')
        return redirect('index')

    if request.method == 'POST':
        form = MeetingForm(request.POST, faculty=request.user)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.save()

            room_name = f"{slugify(meeting.subject.name)}-{meeting.id}"
            room_url = reverse('video_call', kwargs={'room_name': room_name})
            meeting.video_room_link = room_url
            meeting.save()

            students = UserProfile.objects.filter(department=meeting.subject.department, role='student')
            for student_profile in students:
                Notification.objects.create(
                    recipient=student_profile.user,
                    message=(
                        f"New meeting scheduled for subject {meeting.subject.name} "
                        f"on {meeting.schedule_datetime.strftime('%Y-%m-%d %H:%M')}. "
                        f"Join link: {meeting.video_room_link}"
                    )
                )
            messages.success(request, 'Meeting created with video link. Students notified.')
            return redirect('faculty_dashboard')
    else:
        form = MeetingForm(faculty=request.user)

    return render(request, 'main/create_meeting.html', {'form': form})


@login_required
def notifications(request):
    user_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'main/notifications.html', {'notifications': user_notifications})


@login_required
def video_call(request, room_name):
    try:
        meeting = Meeting.objects.get(video_room_link__endswith=f"{room_name}/")
    except Meeting.DoesNotExist:
        return HttpResponseNotFound("Meeting not found for this room")
    
    # Only record attendance for students
    if request.user.userprofile.role == 'student':
        attendance, created = Attendance.objects.get_or_create(
            meeting=meeting,
            student=request.user,
            defaults={'join_time': timezone.now(), 'present': True}
        )
        if not created:
            attendance.join_time = timezone.now()
            attendance.present = True
            attendance.save()
    
    return render(request, 'main/video_call.html', {
        'app_id': 1912473266,
        'server_secret': 'f188564a456fec9ff4ffaf5dcc439678',
        'room_name': room_name,
        'user_id': request.user.id,
        'user_name': request.user.username,
        'meeting': meeting,
    })




@login_required
def edit_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, subject__faculty=request.user)
    if request.method == 'POST':
        form = MeetingForm(request.POST, instance=meeting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Meeting updated successfully.')
            return redirect('faculty_dashboard')
    else:
        form = MeetingForm(instance=meeting)
    return render(request, 'main/edit_meeting.html', {'form': form})


@login_required
def delete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, subject__faculty=request.user)
    if request.method == 'POST':
        meeting.delete()
        messages.success(request, 'Meeting deleted successfully.')
        return redirect('faculty_dashboard')
    return render(request, 'main/confirm_delete.html', {'object': meeting, 'type': 'meeting'})


@login_required
def create_note(request):
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.save()

            students = UserProfile.objects.filter(department=note.subject.department, role='student')
            for student_profile in students:
                Notification.objects.create(
                    recipient=student_profile.user,
                    message=f"New note uploaded for {note.subject.name}: {note.title}"
                )

            messages.success(request, "Note uploaded successfully.")
            return redirect('faculty_notes')
    else:
        form = NoteForm()
    return render(request, 'main/create_note.html', {'form': form})


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, subject__faculty=request.user)
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated successfully.")
            return redirect('faculty_notes')
    else:
        form = NoteForm(instance=note)
    return render(request, 'main/edit_note.html', {'form': form})


@login_required
def delete_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, subject__faculty=request.user)
    if request.method == 'POST':
        note.delete()
        messages.success(request, "Note deleted successfully.")
        return redirect('faculty_notes')
    return render(request, 'main/confirm_delete.html', {'object': note, 'type': 'note'})


@login_required
def faculty_notes(request):
    query = request.GET.get('q')
    notes = Note.objects.filter(subject__faculty=request.user).order_by('-created_at')
    if query:
        notes = notes.filter(title__icontains=query)
    return render(request, 'main/faculty_notes.html', {'notes': notes, 'query': query})


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Meeting, Attendance
import csv

@login_required
def meeting_attendance(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, subject__faculty=request.user)
    attendance_records = Attendance.objects.filter(meeting=meeting).select_related('student')

    # Calculate duration dynamically for display
    for record in attendance_records:
        if record.join_time and record.leave_time:
            record.duration = record.leave_time - record.join_time
        else:
            record.duration = None

    if request.method == 'POST':
        for record in attendance_records:
            present = request.POST.get(f'present_{record.id}', None)
            record.present = present == 'on'
            record.save()
        messages.success(request, "Attendance updated successfully.")
        return redirect('meeting_attendance', meeting_id=meeting_id)

    return render(request, 'main/meeting_attendance.html', {
        'meeting': meeting,
        'attendance_records': attendance_records,
    })

@login_required
def attendance_report(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, subject__faculty=request.user)
    attendance_records = Attendance.objects.filter(meeting=meeting).select_related('student')

    # Calculate duration dynamically for display
    for record in attendance_records:
        if record.join_time and record.leave_time:
            record.duration = record.leave_time - record.join_time
        else:
            record.duration = None

    context = {
        'meeting': meeting,
        'attendance_records': attendance_records,
    }
    return render(request, 'main/attendance_report.html', context)

@login_required
def export_attendance_csv(request, meeting_id):
    meeting = get_object_or_404(Meeting, id=meeting_id, subject__faculty=request.user)
    attendance_records = Attendance.objects.filter(meeting=meeting).select_related('student')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{meeting.subject.name}_{meeting_id}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Present', 'Join Time', 'Leave Time', 'Duration'])

    for record in attendance_records:
        duration = ''
        if record.join_time and record.leave_time:
            duration = str(record.leave_time - record.join_time)
        writer.writerow([
            record.student.get_full_name() or record.student.username,
            'Yes' if record.present else 'No',
            record.join_time.strftime('%Y-%m-%d %H:%M:%S') if record.join_time else '',
            record.leave_time.strftime('%Y-%m-%d %H:%M:%S') if record.leave_time else '',
            duration
        ])

    return response



from .forms import ProfileForm

from django.shortcuts import render, redirect

@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            role = getattr(user.userprofile, 'role', None)
            if role == "student":
                return redirect("student_dashboard")
            elif role == "faculty":
                return redirect("faculty_dashboard")
            else:
                return redirect("index")
        else:
            return render(request, "main/edit_profile.html", {"form": form, "profile": user.userprofile})
    else:
        form = ProfileForm(instance=user)
        return render(request, "main/edit_profile.html", {"form": form, "profile": user.userprofile})





from django.shortcuts import render
from .models import Note  # assuming you have a Note model

from django.shortcuts import render, get_object_or_404
from .models import Note, Attendance, Notification, Subject, Meeting


def student_dashboard(request):
    user = request.user
    department = user.userprofile.department

    # Upcoming meetings for the student’s department subjects
    upcoming_meetings = Meeting.objects.filter(
        subject__department=department,
        schedule_datetime__gte=timezone.now()
    ).order_by('schedule_datetime')

    # Attendance records for the student
    attendances = Attendance.objects.filter(student=user).order_by('-meeting__schedule_datetime')

    # Attendance stats
    total_attendance_records = attendances.count()
    present_count = attendances.filter(present=True).count()
    absent_count = attendances.filter(present=False).count()
    total_attendance = int((present_count / total_attendance_records) * 100) if total_attendance_records > 0 else 0

    # Notes for the department subjects
    notes = Note.objects.filter(subject__department=department).order_by('-created_at')[:5]

    # Notifications for the student
    notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:5]

    context = {
        'upcoming_meetings': upcoming_meetings,
        'attendances': attendances,
        'notes': notes,
        'notifications': notifications,
        'total_attendance': total_attendance,
        'present_count': present_count,
        'absent_count': absent_count,
    }
    return render(request, 'main/student_dashboard.html', context)


def student_notes(request):
    department = request.user.userprofile.department
    notes = Note.objects.filter(subject__department=department).order_by('-created_at')
    context = {'notes': notes}
    return render(request, 'main/student_notes.html', context)

def student_attendance(request):
    attendances = Attendance.objects.filter(student=request.user).order_by('-meeting__schedule_datetime')
    context = {'attendances': attendances}
    return render(request, 'main/student_attendance.html', context)

def student_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    context = {'notifications': notifications}
    return render(request, 'main/student_notifications.html', context)

def download_note(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    if not note.file:
        raise Http404("No file attached.")
    response = FileResponse(open(note.file.path, 'rb'), as_attachment=True, filename=note.file.name)
    return 


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse
import json

@login_required
@csrf_exempt
def attendance_leave(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        meeting_id = data.get('meeting_id')
        user_profile = getattr(request.user, 'userprofile', None)
        if not user_profile or user_profile.role != 'student':
            return JsonResponse({'status': 'error', 'message': 'User is not a student'})
        try:
            attendance = Attendance.objects.get(meeting_id=meeting_id, student=request.user)
            attendance.leave_time = now()
            if attendance.join_time:
                attendance.duration = attendance.leave_time - attendance.join_time
            attendance.save()
            return JsonResponse({'status': 'ok'})
        except Attendance.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Attendance record not found'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'})




#admin

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .models import (
    Department, UserProfile, Subject, Meeting, Note, Attendance, Notification
)

# Decorator to allow only Admin role users
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, "userprofile") and request.user.userprofile.role == "admin":
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return login_required(wrapper)


# Admin Dashboard - landing page, summary or links to sections
@admin_required
def admin_dashboard(request):
    context = {
        "user_count": User.objects.count(),
        "dept_count": Department.objects.count(),
        "subject_count": Subject.objects.count(),
        "meeting_count": Meeting.objects.count(),
        "note_count": Note.objects.count(),
        "attendance_count": Attendance.objects.count(),
        "notification_count": Notification.objects.count(),
    }
    return render(request, "main/admin_dashboard.html", context)


# User management CRUD
@admin_required
def admin_users(request):
    users = User.objects.all()
    return render(request, 'main/admin_users.html', {'users': users})

@admin_required
def admin_add_user(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        department_id = request.POST.get('department')
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username exists")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.department_id = department_id
            profile.save()
            messages.success(request, "User created")
            return redirect('admin_users')
    return render(request, 'main/admin_add_user.html', {'departments': departments})


@admin_required
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        # Create missing UserProfile and assign to user
        profile = UserProfile.objects.create(user=user)

    departments = Department.objects.all()

    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        role = request.POST.get('role')
        department_id = request.POST.get('department')
        user.save()
        profile.role = role
        profile.department_id = department_id
        profile.save()
        messages.success(request, 'User updated')
        return redirect('admin_users')

    return render(request, 'main/admin_edit_user.html', {'user': user, 'profile': profile, 'departments': departments})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted')
        return redirect('admin_users')
    return render(request, 'main/admin_confirm_delete.html', {'object': user, 'type': 'user'})


# Department management CRUD
@admin_required
def admin_departments(request):
    departments = Department.objects.all()
    return render(request, 'main/admin_departments.html', {'departments': departments})

@admin_required
def admin_add_department(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Department.objects.create(name=name)
            messages.success(request, 'Department added')
            return redirect('admin_departments')
    return render(request, 'main/admin_add_department.html')

@admin_required
def admin_edit_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            department.name = name
            department.save()
            messages.success(request, 'Department updated')
            return redirect('admin_departments')
    return render(request, 'main/admin_edit_department.html', {'department': department})

@admin_required
def admin_delete_department(request, department_id):
    department = get_object_or_404(Department, pk=department_id)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted')
        return redirect('admin_departments')
    return render(request, 'main/admin_confirm_delete.html', {'object': department, 'type': 'department'})


# Subject management CRUD
@admin_required
def admin_subjects(request):
    subjects = Subject.objects.all()
    return render(request, 'main/admin_subjects.html', {'subjects': subjects})

@admin_required
def admin_add_subject(request):
    departments = Department.objects.all()
    faculty = UserProfile.objects.filter(role='faculty')
    if request.method == 'POST':
        name = request.POST.get('name')
        dept_id = request.POST.get('department')
        fac_id = request.POST.get('faculty')
        if name and dept_id and fac_id:
            Subject.objects.create(name=name, department_id=dept_id, faculty_id=fac_id)
            messages.success(request, 'Subject added')
            return redirect('admin_subjects')
    return render(request, 'main/admin_add_subject.html', {'departments': departments, 'faculty': faculty})

@admin_required
def admin_edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    departments = Department.objects.all()
    faculty = UserProfile.objects.filter(role='faculty')
    if request.method == 'POST':
        name = request.POST.get('name')
        dept_id = request.POST.get('department')
        fac_id = request.POST.get('faculty')
        if name:
            subject.name = name
        if dept_id:
            subject.department_id = dept_id
        if fac_id:
            subject.faculty_id = fac_id
        subject.save()
        messages.success(request, 'Subject updated')
        return redirect('admin_subjects')
    return render(request, 'main/admin_edit_subject.html', {'subject': subject, 'departments': departments, 'faculty': faculty})

@admin_required
def admin_delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, pk=subject_id)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted')
        return redirect('admin_subjects')
    return render(request, 'main/admin_confirm_delete.html', {'object': subject, 'type': 'subject'})


# Meeting management CRUD
@admin_required
def admin_meetings(request):
    meetings = Meeting.objects.select_related('subject', 'subject__faculty').all()
    return render(request, 'main/admin_meetings.html', {'meetings': meetings})

@admin_required
def admin_add_meeting(request):
    subjects = Subject.objects.all()
    if request.method == 'POST':
        subject_id = request.POST.get("subject")
        schedule = request.POST.get("schedule_datetime")
        link = request.POST.get("meeting_link")
        if subject_id and schedule:
            Meeting.objects.create(subject_id=subject_id, schedule_datetime=schedule, meeting_link=link)
            messages.success(request, "Meeting Added")
            return redirect('admin_meetings')
    return render(request, 'main/admin_add_meeting.html', {'subjects': subjects})

@admin_required
def admin_edit_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    subjects = Subject.objects.all()
    if request.method == 'POST':
        subject_id = request.POST.get("subject")
        schedule = request.POST.get("schedule_datetime")
        link = request.POST.get("meeting_link")
        if subject_id and schedule:
            meeting.subject_id = subject_id
            meeting.schedule_datetime = schedule
            meeting.meeting_link = link
            meeting.save()
            messages.success(request, "Meeting Updated")
            return redirect('admin_meetings')
    return render(request, 'main/admin_edit_meeting.html', {'meeting': meeting, 'subjects': subjects})

@admin_required
def admin_delete_meeting(request, meeting_id):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if request.method == 'POST':
        meeting.delete()
        messages.success(request, "Meeting Deleted")
        return redirect('admin_meetings')
    return render(request, 'main/admin_confirm_delete.html', {'object': meeting, 'type': 'meeting'})


# Note management CRUD
@admin_required
def admin_notes(request):
    notes = Note.objects.select_related('subject').all()
    return render(request, 'main/admin_notes.html', {'notes': notes})

@admin_required
def admin_add_note(request):
    subjects = Subject.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        subject_id = request.POST.get('subject')
        if title and subject_id:
            Note.objects.create(title=title, content=content, subject_id=subject_id)
            messages.success(request, 'Note added')
            return redirect('admin_notes')
    return render(request, 'main/admin_add_note.html', {'subjects': subjects})

@admin_required
def admin_edit_note(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    subjects = Subject.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        subject_id = request.POST.get('subject')
        if title and subject_id:
            note.title = title
            note.content = content
            note.subject_id = subject_id
            note.save()
            messages.success(request, 'Note updated')
            return redirect('admin_notes')
    return render(request, 'main/admin_edit_note.html', {'note': note, 'subjects': subjects})

@admin_required
def admin_delete_note(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    if request.method == 'POST':
        note.delete()
        messages.success(request, "Note deleted")
        return redirect('admin_notes')
    return render(request, 'main/admin_confirm_delete.html', {'object': note, 'type': 'note'})


# Attendance management
@admin_required
def admin_attendance(request):
    attendance_records = Attendance.objects.select_related('student', 'meeting').all()
    return render(request, 'main/admin_attendance.html', {'attendance_records': attendance_records})

# For full CRUD on attendance, you’d probably manage attendance through meeting management screens or reports.

# Notifications management
@admin_required
def admin_notifications(request):
    notifications = Notification.objects.select_related('recipient').all()
    return render(request, "main/admin_notifications.html", {"notifications": notifications})

@admin_required
def admin_delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    if request.method == "POST":
        notification.delete()
        messages.success(request, "Notification deleted")
        return redirect("admin_notifications")
    return render(request, "main/admin_confirm_delete.html", {"object": notification, "type": "notification"})
