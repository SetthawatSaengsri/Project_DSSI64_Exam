#forms.py

from django.forms.widgets import DateInput, DateTimeInput,Select,TimeInput
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *
from django.forms import ModelForm
import pytz

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
    ROOM_ASSIGNMENT_CHOICES = [
        ('auto', 'จัดห้องอัตโนมัติ'),
        ('manual', 'เลือกห้องเอง'),
    ]
    
    term = forms.ChoiceField(
        choices=ExamSubject.TERM_CHOICES,
        required=True,
        label="ภาคเรียน"
    )
    
    student_class = forms.ChoiceField(
        choices=[],
        required=True,
        label="ระดับชั้น"
    )
    
    room_assignment_type = forms.ChoiceField(
        choices=ROOM_ASSIGNMENT_CHOICES,
        required=True,
        label="วิธีการจัดห้องสอบ",
        initial='auto',  # ตั้งค่าเริ่มต้นเป็น auto
        widget=forms.RadioSelect(attrs={'class': 'room-assignment-radio'})
    )
    
    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        required=False,
        label="อาคาร",
        empty_label="เลือกอาคาร"
    )
    
    # Override room field to make it optional initially
    room = forms.ModelChoiceField(
        queryset=ExamRoom.objects.none(),
        required=False,
        label="ห้องสอบ",
        empty_label="เลือกห้องสอบ"
    )

    class Meta:
        model = ExamSubject
        fields = [
            'subject_name', 'subject_code', 'academic_year', 'term',
            'exam_date', 'start_time', 'end_time',
            'room_assignment_type', 'building', 'room', 
            'invigilator', 'secondary_invigilator', 'student_class'
        ]
        widgets = {
            'exam_date': DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'start_time': TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control',
                'step': '300'  # 5-minute intervals
            }),
            'end_time': TimeInput(attrs={
                'type': 'time', 
                'class': 'form-control',
                'step': '300'  # 5-minute intervals
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            # Filter teachers by school
            teacher_qs = TeacherProfile.objects.filter(user__school_name=user.school_name)
            self.fields['invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].queryset = teacher_qs
            self.fields['secondary_invigilator'].required = False

            # Get student classes for this school
            student_classes = StudentProfile.objects.filter(
                user__school_name=user.school_name
            ).values_list('student_class', flat=True).distinct()

            self.fields['student_class'].choices = [("", "เลือกระดับชั้น")] + [
                (sc, sc) for sc in student_classes if sc
            ]

            # Set up building and room querysets
            self.fields['building'].queryset = Building.objects.all().order_by('code')
            
            # If building is selected, filter rooms
            if 'building' in self.data:
                try:
                    building_id = int(self.data.get('building'))
                    self.fields['room'].queryset = ExamRoom.objects.filter(
                        building_id=building_id
                    ).order_by('name')
                except (ValueError, TypeError):
                    pass
            elif self.instance.pk and hasattr(self.instance, 'room') and self.instance.room:
                # For editing existing instances
                self.fields['room'].queryset = ExamRoom.objects.filter(
                    building=self.instance.room.building
                ).order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        room_assignment_type = cleaned_data.get("room_assignment_type")
        room = cleaned_data.get("room")
        building = cleaned_data.get("building")

        # Validate time
        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "เวลาสิ้นสุดต้องมากกว่าเวลาเริ่ม")

        # Validate room selection for manual assignment
        if room_assignment_type == 'manual':
            if not building:
                self.add_error('building', "กรุณาเลือกอาคาร")
            if not room:
                self.add_error('room', "กรุณาเลือกห้องสอบ")

        return cleaned_data

    def save(self, commit=True):
        subject = super().save(commit=False)
        
        # หมายเหตุ: การแปลงเวลาจะทำใน view แทน เพราะที่นี่ยังเป็น time object
        # ไม่ต้องแปลง timezone ที่นี่
        
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


    
