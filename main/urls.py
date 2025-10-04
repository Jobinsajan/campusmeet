from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/meeting/create/', views.create_meeting, name='create_meeting'),
    path('notifications/', views.notifications, name='notifications'),
    path('videocall/room/<str:room_name>/', views.video_call, name='video_call'),

    path('faculty/meeting/<int:meeting_id>/edit/', views.edit_meeting, name='edit_meeting'),
    path('faculty/meeting/<int:meeting_id>/delete/', views.delete_meeting, name='delete_meeting'),
    path('faculty/notes/', views.faculty_notes, name='faculty_notes'),
    path('faculty/notes/create/', views.create_note, name='create_note'),
    path('faculty/notes/<int:note_id>/edit/', views.edit_note, name='edit_note'),
    path('faculty/notes/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('faculty/meeting/<int:meeting_id>/attendance/', views.meeting_attendance, name='meeting_attendance'),
    path('faculty/meeting/<int:meeting_id>/attendance_report/', views.attendance_report, name='attendance_report'),
    path('faculty/meeting/<int:meeting_id>/attendance_report/export_csv/', views.export_attendance_csv, name='export_attendance_csv'),
    path('faculty/profile/edit/', views.edit_profile, name='edit_profile'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Add these new patterns for student views
    path('student/notes/', views.student_notes, name='student_notes'),
    path('student/notes/<int:note_id>/download/', views.download_note, name='download_note'),  # optional for downloads
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('attendance/leave/', views.attendance_leave, name='attendance_leave'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),

    # Admin dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # User management
    path('users/', views.admin_users, name='admin_users'),
    path('users/add/', views.admin_add_user, name='admin_add_user'),
    path('users/edit/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('users/delete/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),

    # Department management
    path('departments/', views.admin_departments, name='admin_departments'),
    path('departments/add/', views.admin_add_department, name='admin_add_department'),
    path('departments/edit/<int:department_id>/', views.admin_edit_department, name='admin_edit_department'),
    path('departments/delete/<int:department_id>/', views.admin_delete_department, name='admin_delete_department'),

    # Subject management
    path('subjects/', views.admin_subjects, name='admin_subjects'),
    path('subjects/add/', views.admin_add_subject, name='admin_add_subject'),
    path('subjects/edit/<int:subject_id>/', views.admin_edit_subject, name='admin_edit_subject'),
    path('subjects/delete/<int:subject_id>/', views.admin_delete_subject, name='admin_delete_subject'),

    # Meeting management
    path('meetings/', views.admin_meetings, name='admin_meetings'),
    path('meetings/add/', views.admin_add_meeting, name='admin_add_meeting'),
    path('meetings/edit/<int:meeting_id>/', views.admin_edit_meeting, name='admin_edit_meeting'),
    path('meetings/delete/<int:meeting_id>/', views.admin_delete_meeting, name='admin_delete_meeting'),

    # Note management
    path('notes/', views.admin_notes, name='admin_notes'),
    path('notes/add/', views.admin_add_note, name='admin_add_note'),
    path('notes/edit/<int:note_id>/', views.admin_edit_note, name='admin_edit_note'),
    path('notes/delete/<int:note_id>/', views.admin_delete_note, name='admin_delete_note'),

    # Attendance review
    path('attendance/', views.admin_attendance, name='admin_attendance'),

    # Notifications management
    path('notifications/', views.admin_notifications, name='admin_notifications'),
    path('notifications/delete/<int:notification_id>/', views.admin_delete_notification, name='admin_delete_notification'),
]
