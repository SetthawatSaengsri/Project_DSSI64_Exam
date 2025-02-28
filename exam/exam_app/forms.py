#forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms.widgets import DateTimeInput,Select
from django.forms import ModelForm


class StudentRegistrationForm(UserCreationForm):
    student_id = forms.CharField(max_length=10)
    no_student = forms.CharField(max_length=10)
    student_class = forms.CharField(max_length=20)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'student_id', 'no_student', 'student_class']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        user.school_name = self.cleaned_data.get('school_name')  # ดึง school_name จากแบบฟอร์ม
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                no_student=self.cleaned_data['no_student'],
                student_class=self.cleaned_data['student_class']
            )
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


class StaffRegistrationForm(UserCreationForm):
    school_name = forms.CharField(max_length=100, required=True, label="โรงเรียน")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
            # Save additional information, such as school name
            profile = StaffProfile.objects.create(user=user, school_name=self.cleaned_data['school_name'])
        return user

class ExamSubjectForm(forms.ModelForm):
    student_class = forms.ChoiceField(
        choices=[],  # จะถูกตั้งค่าใน `__init__`
        required=True,
        label="ระดับชั้น",
    )

    class Meta:
        model = ExamSubject
        fields = [
            'subject_name', 'subject_code', 'academic_year', 'exam_date',
            'start_time', 'end_time', 'room', 'invigilator', 'student_class'
        ]
        widgets = {
            'exam_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # ดึงรายชื่อครูที่อยู่ในโรงเรียนเดียวกัน
            self.fields['invigilator'].queryset = TeacherProfile.objects.filter(user__school_name=user.school_name)

            # ดึงระดับชั้นจากนักเรียนในโรงเรียนเดียวกัน
            student_classes = StudentProfile.objects.filter(
                user__school_name=user.school_name
            ).values_list('student_class', flat=True).distinct()

            # ตั้งค่า choices
            self.fields['student_class'].choices = [("", "เลือกระดับชั้น")] + [(sc, sc) for sc in student_classes if sc]

            # Debug เช็คข้อมูลระดับชั้นที่ดึงมา
            print("ระดับชั้นที่ดึงมา:", list(student_classes))
    
