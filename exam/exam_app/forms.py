#forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms.widgets import DateTimeInput,Select
from django.forms import ModelForm

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'school_name', 'is_active', 'is_student', 'is_teacher', 'is_staff'
        ]

# ฟอร์มสำหรับแก้ไขข้อมูล User (นักเรียน)
class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# ฟอร์มสำหรับแก้ไขข้อมูล StudentProfile
class StudentProfileEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['student_id', 'no_student', 'student_class']
                
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
    id_card = forms.FileField(required=True, label="ไฟล์หลักฐานบัตรประจำตัว")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'school_name', 'id_card']

    def save(self, commit=True):
        # Create the user object but do not save it yet
        user = super().save(commit=False)
        user.is_staff = True
        user.is_active = False  # ตั้งค่าให้ไม่ได้รับการอนุมัติจนกว่าจะได้รับการอนุมัติจากแอดมิน

        if commit:
            # Save the user first
            user.save()

            # Save the school name to the StaffProfile model
            profile = StaffProfile.objects.create(user=user, school_name=self.cleaned_data['school_name'])

            # Save the uploaded ID card
            uploaded_file = self.cleaned_data['id_card']
            profile.id_card = uploaded_file
            profile.save()

        return user


class ExamSubjectForm(forms.ModelForm):
    
    student_class = forms.ChoiceField(
        choices=[],  
        required=True,
        label="ระดับชั้น"
    )

    class Meta:
        model = ExamSubject
        fields = [
            'subject_name', 'subject_code', 'academic_year', 'exam_date',
            'start_time', 'end_time', 'room', 'invigilator', 'secondary_invigilator',
            'student_class'
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
            teacher_qs = TeacherProfile.objects.filter(user__school_name=user.school_name)
            self.fields['invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].required = False

            # ดึงระดับชั้นจากนักเรียนในโรงเรียนเดียวกัน
            student_classes = StudentProfile.objects.filter(
                user__school_name=user.school_name
            ).values_list('student_class', flat=True).distinct()

            # ตั้งค่า choices สำหรับระดับชั้น
            self.fields['student_class'].choices = [("", "เลือกระดับชั้น")] + [(sc, sc) for sc in student_classes if sc]

            # Debug: แสดงระดับชั้นที่ดึงมา
            print("ระดับชั้นที่ดึงมา:", list(student_classes))

    def save(self, commit=True):
        subject = super().save(commit=False)
        # กำหนดค่า qr_expiration โดยอัตโนมัติจาก end_time
        subject.qr_expiration = subject.end_time
        if commit:
            subject.save()
            self.save_m2m()
        return subject


    
