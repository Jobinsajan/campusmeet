from django import forms
from .models import Meeting, Subject, Note
from django.contrib.auth.models import User
from .models import UserProfile


class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['subject', 'schedule_datetime']  # Exclude meeting_link field

    def __init__(self, *args, **kwargs):
        faculty = kwargs.pop('faculty', None)
        super().__init__(*args, **kwargs)
        if faculty:
            self.fields['subject'].queryset = Subject.objects.filter(faculty=faculty)


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['subject', 'title', 'content', 'file']


from django import forms
from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control form-control-sm',
        'aria-label': 'Profile Image upload'
    }))

    class Meta:
        model = User
        fields = ['username']  # username field only
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'aria-label': 'Username',
                'placeholder': 'Enter your username'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['profile_image'].initial = getattr(self.instance.userprofile, 'profile_image', None)

    def save(self, commit=True):
        user = super().save(commit=commit)
        profile_image = self.cleaned_data.get('profile_image')
        profile = user.userprofile
        if profile_image:
            profile.profile_image = profile_image
            if commit:
                profile.save()
        return user


