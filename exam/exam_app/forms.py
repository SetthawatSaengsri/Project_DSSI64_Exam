#forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms.widgets import DateTimeInput


class StudentRegistrationForm(UserCreationForm):
    student_id = forms.CharField(max_length=10)
    no_student = forms.CharField(max_length=10)
    student_class = forms.ChoiceField(choices=StudentProfile.CLASS_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'student_id', 'no_student', 'student_class']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            StudentProfile.objects.create(user=user, student_id=self.cleaned_data['student_id'], no_student=self.cleaned_data['no_student'], student_class=self.cleaned_data['student_class'])
        return user


class TeacherRegistrationForm(UserCreationForm):
    teacher_id = forms.CharField(max_length=10)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'teacher_id']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        if commit:
            user.save()
            TeacherProfile.objects.create(
                user=user, 
                teacher_id=self.cleaned_data['teacher_id'],
            )
        return user



class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'student_class']


class ExamSubjectForm(forms.ModelForm):
    invigilator = forms.ModelChoiceField(
        queryset=TeacherProfile.objects.all(),
        label="Invigilator",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    subject_teacher = forms.ModelChoiceField(
        queryset=TeacherProfile.objects.all(),
        label="Subject Teacher",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    student_class = forms.ModelChoiceField(
        queryset=StudentProfile.objects.all(),
        label="Student Class",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    students = forms.ModelMultipleChoiceField(
        queryset=StudentProfile.objects.none(),  # กำหนด queryset เริ่มต้นเป็น none
        label="Registered Students",
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
    )
    exam_room = forms.ModelChoiceField(
        queryset=ExamRoom.objects.all(),
        label="Exam Room",
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    start_time = forms.DateTimeField(
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='Start Time',
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    end_time = forms.DateTimeField(
        widget=DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        label='End Time',
        input_formats=['%Y-%m-%dT%H:%M'],
    )

    class Meta:
        model = ExamSubject
        fields = ['subject_name', 'subject_code', 'academic_year', 'student_class', 'exam_room', 'start_time', 'end_time', 'invigilator', 'subject_teacher', 'students']

    def __init__(self, *args, **kwargs):
        super(ExamSubjectForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['students'].queryset = StudentProfile.objects.filter(student_class=self.instance.student_class)
        else:
            self.fields['students'].queryset = StudentProfile.objects.none()

        if 'initial' in kwargs and 'student_class' in kwargs['initial']:
            student_class_id = kwargs['initial']['student_class']
            self.fields['students'].queryset = StudentProfile.objects.filter(student_class=student_class_id)

    def save(self, commit=True):
        instance = super(ExamSubjectForm, self).save(commit=False)
        if commit:
            instance.save()
            if 'students' in self.cleaned_data:
                instance.students.set(self.cleaned_data['students'])
            self.save_m2m()
        return instance
