#forms.py

from django.forms.widgets import DateInput, DateTimeInput
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
            'exam_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # ใช้ DateInput สำหรับวันที่
            'start_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),  # ใช้ DateTimeInput สำหรับเวลา
            'end_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),  # ใช้ DateTimeInput สำหรับเวลา
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # รับ user จาก view
        super().__init__(*args, **kwargs)

        if user:
            # กรองครูในโรงเรียนเดียวกัน
            teacher_qs = TeacherProfile.objects.filter(user__school_name=user.school_name)
            self.fields['invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].required = False

            # กรองห้องสอบทั้งหมด (ถ้ามีฟิลด์ school_name ในอนาคต สามารถกรองเพิ่มได้)
            room_qs = ExamRoom.objects.all().order_by('name')
            self.fields['room'].queryset = room_qs
            self.fields['room'].empty_label = "เลือกห้องสอบ"

            # ดึงระดับชั้นจากนักเรียนโรงเรียนเดียวกัน และจัดเรียงแบบไม่ซ้ำ
            student_classes = StudentProfile.objects.filter(
                user__school_name=user.school_name
            ).values_list('student_class', flat=True).distinct()

            self.fields['student_class'].choices = [("", "เลือกระดับชั้น")] + [(sc, sc) for sc in student_classes if sc]

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม")

        return cleaned_data

    def save(self, commit=True):
        subject = super().save(commit=False)
        # ตั้งค่าเวลาหมดอายุ QR เป็นเวลาสิ้นสุดสอบ
        subject.qr_expiration = subject.end_time.time() if subject.end_time else None

        if commit:
            subject.save()
            self.save_m2m()
        return subject


class ExamRoomForm(forms.ModelForm):
    class Meta:
        model = ExamRoom
        fields = ['building', 'name', 'capacity']  # ต้องเพิ่ม 'building'
        widgets = {
            'building': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ชื่อห้อง'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'ความจุ'}),
        }
        labels = {
            'building': 'อาคาร',
            'name': 'ชื่อห้องสอบ',
            'capacity': 'ความจุ (จำนวนคน)',
        }


class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['code', 'name']
        labels = {
            'code': 'รหัสอาคาร',
            'name': 'ชื่ออาคาร',
        }


    
