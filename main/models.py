

# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g. MCA, MSC, MBA

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='profile_images/', default='default_profile.png')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role}, {self.department})"


    



class Subject(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'faculty'})

    def __str__(self):
        return f"{self.name} ({self.department.name})"

class Meeting(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    schedule_datetime = models.DateTimeField()
    meeting_link = models.URLField(blank=True, null=True)  # Placeholder for video call link
    video_room_link = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.subject.name} on {self.schedule_datetime.strftime('%Y-%m-%d %H:%M')}"

class Note(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='notes/', blank=True, null=True)  # For attachments
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Attendance(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'userprofile__role': 'student'})
    join_time = models.DateTimeField(null=True, blank=True)
    leave_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    present = models.BooleanField(default=False)  # Marked True if attendance criteria met

    def __str__(self):
        return f"{self.student.username} - {self.meeting.subject.name} - {'Present' if self.present else 'Absent'}"

    def save(self, *args, **kwargs):
        if self.join_time and self.leave_time:
            self.duration = self.leave_time - self.join_time
        else:
            self.duration = None
        super().save(*args, **kwargs)

    


from django.utils import timezone

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.recipient.username} - {'Read' if self.read else 'Unread'}"

