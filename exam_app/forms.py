from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time

import pandas as pd

from .models import (
    User,
    StudentProfile,
    TeacherProfile,
    ExamRoom,
    ExamSubject,
    Building,
    Attendance,
)

# ==============================================================================
# ฟอร์มจัดการผู้ใช้/โปรไฟล์
# ==============================================================================

class UserEditForm(forms.ModelForm):
    """ฟอร์มแก้ไขข้อมูลผู้ใช้ (สำหรับแอดมิน)"""
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'is_active', 'is_student', 'is_teacher', 'is_superuser'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'is_superuser': 'ผู้ดูแลระบบ (Admin)',
            'is_student': 'นักเรียน',
            'is_teacher': 'ครู',
            'is_active': 'ใช้งานได้',
        }


class StudentRegistrationForm(UserCreationForm):
    """ฟอร์มสมัครสมาชิกนักเรียน"""
    student_id = forms.CharField(max_length=20, label="รหัสนักเรียน")
    student_number = forms.CharField(max_length=10, label="เลขที่")
    student_class = forms.CharField(max_length=20, label="ระดับชั้น")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ['username', 'first_name', 'last_name', 'email', 'password1', 'password2',
                     'student_id', 'student_number', 'student_class']:
            self.fields[name].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_student = True
        if commit:
            user.save()
            StudentProfile.objects.create(
                user=user,
                student_id=self.cleaned_data['student_id'],
                student_number=self.cleaned_data['student_number'],
                student_class=self.cleaned_data['student_class'],
            )
        return user


class TeacherRegistrationForm(UserCreationForm):
    """ฟอร์มสมัครสมาชิกครู"""
    teacher_id = forms.CharField(max_length=20, label="รหัสครู")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

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


class AdminRegistrationForm(UserCreationForm):
    """ฟอร์มสมัครสมาชิกผู้ดูแลระบบ (Admin)"""
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'ชื่อผู้ใช้',
            'first_name': 'ชื่อจริง',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
            'password1': 'รหัสผ่าน',
            'password2': 'ยืนยันรหัสผ่าน',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_superuser = True
        user.is_staff = True  # Django's built-in staff flag
        if commit:
            user.save()
        return user


class UserProfileEditForm(forms.ModelForm):
    """ฟอร์มแก้ไขโปรไฟล์ผู้ใช้"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'ชื่อจริง',
            'last_name': 'นามสกุล',
            'email': 'อีเมล',
        }


class StudentProfileEditForm(forms.ModelForm):
    """ฟอร์มแก้ไขโปรไฟล์นักเรียน"""
    class Meta:
        model = StudentProfile
        fields = ['student_id', 'student_number', 'student_class']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'student_number': forms.TextInput(attrs={'class': 'form-control'}),
            'student_class': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'student_id': 'รหัสนักเรียน',
            'student_number': 'เลขที่',
            'student_class': 'ระดับชั้น',
        }


class TeacherProfileEditForm(forms.ModelForm):
    """ฟอร์มแก้ไขโปรไฟล์ครู"""
    class Meta:
        model = TeacherProfile
        fields = ['teacher_id', 'department']
        widgets = {
            'teacher_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'teacher_id': 'รหัสครู',
            'department': 'แผนก/กลุ่มสาระ',
        }


# ==============================================================================
# ฟอร์ม Import ข้อมูลผู้ใช้
# ==============================================================================

class StudentImportForm(forms.Form):
    """ฟอร์มสำหรับ import ข้อมูลนักเรียน"""
    file = forms.FileField(
        label="ไฟล์ข้อมูลนักเรียน",
        help_text="รองรับไฟล์ .xlsx, .xls, .csv",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )
    overwrite_existing = forms.BooleanField(
        label="อัปเดตข้อมูลที่มีอยู่แล้ว",
        required=False,
        initial=False,
        help_text="หากเลือก จะอัปเดตข้อมูลนักเรียนที่มีรหัสซ้ำ"
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("ไฟล์ใหญ่เกินไป (สูงสุด 5MB)")
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in ['.xlsx', '.xls', '.csv']:
            raise ValidationError("รองรับเฉพาะ .xlsx, .xls, .csv")
        return file

    def process_file(self):
        file = self.cleaned_data['file']
        ext = '.' + file.name.split('.')[-1].lower()
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file)
            else:
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='tis-620')
            required = ['username', 'password', 'student_id', 'first_name', 'last_name',
                        'email', 'student_class', 'student_number']
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise ValidationError(f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missing)}")

            df = df.dropna(subset=required).fillna('')
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            return df.to_dict('records')
        except Exception as e:
            raise ValidationError(f"ไม่สามารถอ่านไฟล์ได้: {e}")


class TeacherImportForm(forms.Form):
    """ฟอร์มสำหรับ import ข้อมูลครู"""
    file = forms.FileField(
        label="ไฟล์ข้อมูลครู",
        help_text="รองรับไฟล์ .xlsx, .xls, .csv",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls,.csv'
        })
    )
    overwrite_existing = forms.BooleanField(
        label="อัปเดตข้อมูลที่มีอยู่แล้ว",
        required=False,
        initial=False,
        help_text="หากเลือก จะอัปเดตข้อมูลครูที่มีรหัสซ้ำ"
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 5 * 1024 * 1024:
            raise ValidationError("ไฟล์ใหญ่เกินไป (สูงสุด 5MB)")
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in ['.xlsx', '.xls', '.csv']:
            raise ValidationError("รองรับเฉพาะ .xlsx, .xls, .csv")
        return file

    def process_file(self):
        file = self.cleaned_data['file']
        ext = '.' + file.name.split('.')[-1].lower()
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file)
            else:
                try:
                    df = pd.read_csv(file, encoding='utf-8')
                except UnicodeDecodeError:
                    file.seek(0)
                    df = pd.read_csv(file, encoding='tis-620')
            required = ['username', 'password', 'teacher_id', 'first_name', 'last_name', 'email']
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise ValidationError(f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missing)}")

            df = df.dropna(subset=required).fillna('')
            for col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].astype(str).str.strip()
            return df.to_dict('records')
        except Exception as e:
            raise ValidationError(f"ไม่สามารถอ่านไฟล์ได้: {e}")


# ==============================================================================
# ฟอร์มรายวิชา/การสอบ
# ==============================================================================

class ExamSubjectForm(forms.ModelForm):
    """ฟอร์มสำหรับเพิ่ม/แก้ไขรายวิชาสอบ"""

    student_class = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
            'placeholder': 'เช่น ม.1/1, ม.2/1'
        }),
        label='ระดับชั้น'
    )

    auto_assign_room = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500'
        }),
        label='จัดห้องสอบอัตโนมัติ'
    )

    auto_assign_teachers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-5 h-5 text-blue-600 bg-slate-700 border-slate-600 rounded focus:ring-blue-500'
        }),
        label='จัดครูคุมสอบอัตโนมัติ'
    )

    class Meta:
        model = ExamSubject
        fields = [
            'subject_name', 'subject_code', 'academic_year', 'term',
            'exam_date', 'start_time', 'end_time', 'room',
            'invigilator', 'secondary_invigilator', 'instructions',
        ]
        widgets = {
            'subject_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
                'placeholder': 'ชื่ออย่างเต็มของวิชา'
            }),
            'subject_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
                'placeholder': 'เช่น MATH101'
            }),
            'academic_year': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
                'placeholder': 'เช่น 2568'
            }),
            'term': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'exam_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'room': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'invigilator': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'secondary_invigilator': forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
                'rows': 4,
                'placeholder': 'คำแนะนำพิเศษสำหรับการสอบ (ถ้ามี)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ค่าเริ่มต้นปี พ.ศ.
        self.fields['academic_year'].initial = str(timezone.now().year + 543)

        # Querysets
        self.fields['room'].queryset = ExamRoom.objects.filter(is_active=True).select_related('building')
        self.fields['room'].empty_label = "เลือกห้องสอบ"

        teacher_qs = TeacherProfile.objects.select_related('user').filter(user__is_active=True)
        self.fields['invigilator'].queryset = teacher_qs
        self.fields['invigilator'].empty_label = "เลือกครูคุมสอบหลัก"
        self.fields['secondary_invigilator'].queryset = teacher_qs
        self.fields['secondary_invigilator'].empty_label = "เลือกครูคุมสอบสำรอง"

    def clean(self):
        cleaned = super().clean()
        exam_date = cleaned.get('exam_date')
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        room = cleaned.get('room')
        invigilator = cleaned.get('invigilator')
        secondary_invigilator = cleaned.get('secondary_invigilator')

        # ตรวจสอบเวลา
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('เวลาเริ่มต้องน้อยกว่าเวลาสิ้นสุด')
            # ขั้นต่ำ 30 นาที
            start_dt = datetime.combine(timezone.now().date(), start_time)
            end_dt = datetime.combine(timezone.now().date(), end_time)
            if (end_dt - start_dt).total_seconds() < 1800:
                raise ValidationError('การสอบต้องมีระยะเวลาอย่างน้อย 30 นาที')

        # ตรวจสอบวันที่ต้องเป็นอนาคต
        if exam_date and exam_date < timezone.now().date():
            raise ValidationError('วันที่สอบต้องเป็นวันที่ในอนาคต')

        # ห้องซ้อนเวลา
        if all([exam_date, start_time, end_time, room]):
            conflicts = ExamSubject.objects.filter(
                room=room,
                exam_date=exam_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise ValidationError(f'ห้อง {room} ไม่ว่างในช่วงเวลาดังกล่าว')

        # ครูหลัก/สำรองต้องไม่ซ้ำกัน
        if invigilator and secondary_invigilator and invigilator == secondary_invigilator:
            raise ValidationError('ครูคุมสอบหลักและสำรองต้องเป็นคนละคน')

        # ความพร้อมของครู
        if all([exam_date, start_time, end_time, invigilator]):
            busy_primary = ExamSubject.objects.filter(
                invigilator=invigilator,
                exam_date=exam_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            busy_secondary = ExamSubject.objects.filter(
                secondary_invigilator=invigilator,
                exam_date=exam_date,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance.pk:
                busy_primary = busy_primary.exclude(pk=self.instance.pk)
                busy_secondary = busy_secondary.exclude(pk=self.instance.pk)
            if busy_primary.exists() or busy_secondary.exists():
                raise ValidationError(f'{invigilator.user.get_full_name()} ไม่ว่างในช่วงเวลาดังกล่าว')

        return cleaned


class ExamSubjectSearchForm(forms.Form):
    """ฟอร์มสำหรับค้นหาและกรองรายวิชาสอบ"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
            'placeholder': 'ค้นหาชื่อวิชา หรือรหัสวิชา...'
        }),
        label='ค้นหา'
    )

    class_filter = forms.CharField(required=False, label='ระดับชั้น')
    year_filter = forms.CharField(required=False, label='ปีการศึกษา')

    status_filter = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'ทั้งหมด'),
            ('upcoming', 'จะมาถึง'),
            ('ongoing', 'กำลังสอบ'),
            ('completed', 'สิ้นสุดแล้ว'),
            ('incomplete_assignment', 'จัดครู/ห้องไม่สมบูรณ์'),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
        }),
        label='สถานะ'
    )

    def __init__(self, *args, **kwargs):
        classes = kwargs.pop('classes', [])
        years = kwargs.pop('years', [])
        super().__init__(*args, **kwargs)

        self.fields['class_filter'] = forms.ChoiceField(
            required=False,
            choices=[('', 'ทั้งหมด')] + [(c, c) for c in classes],
            widget=forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            label='ระดับชั้น'
        )

        self.fields['year_filter'] = forms.ChoiceField(
            required=False,
            choices=[('', 'ทั้งหมด')] + [(y, y) for y in years],
            widget=forms.Select(attrs={
                'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
            }),
            label='ปีการศึกษา'
        )


class ExamSubjectImportForm(forms.Form):
    """ฟอร์ม Import รายวิชาสอบจากไฟล์"""
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': '.xlsx,.xls,.csv'
        }),
        required=True,
        help_text="อัพโหลดไฟล์ Excel (.xlsx, .xls) หรือ CSV"
    )
    
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-purple-500 bg-slate-700 border-slate-600 rounded focus:ring-purple-500'
        }),
        label="อัปเดตข้อมูลที่มีอยู่แล้ว"
    )
    
    auto_assign_resources = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-purple-500 bg-slate-700 border-slate-600 rounded focus:ring-purple-500'
        }),
        label="จัดครูและห้องสอบอัตโนมัติ"
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise ValidationError("กรุณาเลือกไฟล์")
        
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise ValidationError("กรุณาเลือกไฟล์ .xlsx, .xls หรือ .csv เท่านั้น")
        
        if file.size > 50 * 1024 * 1024:
            raise ValidationError("ไฟล์มีขนาดใหญ่เกิน 50MB")
        
        return file
    
    def process_file(self):
        """ประมวลผลไฟล์และแปลงเป็นข้อมูล"""
        file = self.cleaned_data['file']
        file_extension = file.name.lower().split('.')[-1]
        
        try:
            if file_extension == 'csv':
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file, engine='openpyxl')
            
            df.columns = df.columns.str.strip()
            
            required_columns = [
                'subject_name', 'subject_code', 'academic_year', 'term',
                'exam_date', 'start_time', 'end_time', 'student_class'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValidationError(f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missing_columns)}")
            
            df = df.dropna(how='all')
            
            if df.empty:
                raise ValidationError("ไฟล์ไม่มีข้อมูล")
            
            subjects_data = []
            for index, row in df.iterrows():
                try:
                    subject_data = {
                        'subject_name': str(row['subject_name']).strip() if pd.notna(row['subject_name']) else '',
                        'subject_code': str(row['subject_code']).strip() if pd.notna(row['subject_code']) else '',
                        'academic_year': str(row['academic_year']).strip() if pd.notna(row['academic_year']) else '',
                        'term': str(row['term']).strip() if pd.notna(row['term']) else '',
                        'student_class': str(row['student_class']).strip() if pd.notna(row['student_class']) else '',
                    }
                    
                    # แปลงวันที่
                    if pd.notna(row['exam_date']):
                        if isinstance(row['exam_date'], str):
                            date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
                            exam_date = None
                            for fmt in date_formats:
                                try:
                                    exam_date = datetime.strptime(row['exam_date'], fmt).date()
                                    break
                                except ValueError:
                                    continue
                            
                            if exam_date is None:
                                raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: {row['exam_date']}")
                            
                            subject_data['exam_date'] = exam_date
                        else:
                            subject_data['exam_date'] = pd.to_datetime(row['exam_date']).date()
                    else:
                        subject_data['exam_date'] = None
                    
                    # แปลงเวลา
                    for time_field in ['start_time', 'end_time']:
                        if pd.notna(row[time_field]):
                            if isinstance(row[time_field], str):
                                try:
                                    time_obj = datetime.strptime(row[time_field], '%H:%M').time()
                                    subject_data[time_field] = time_obj
                                except ValueError:
                                    raise ValueError(f"รูปแบบเวลาไม่ถูกต้อง: {row[time_field]} (ใช้รูปแบบ HH:MM)")
                            elif isinstance(row[time_field], datetime):
                                subject_data[time_field] = row[time_field].time()
                            else:
                                subject_data[time_field] = row[time_field]
                        else:
                            subject_data[time_field] = None
                    
                    subjects_data.append(subject_data)
                    
                except Exception as e:
                    raise ValidationError(f"ข้อผิดพลาดในแถว {index + 2}: {str(e)}")
            
            return subjects_data
            
        except pd.errors.EmptyDataError:
            raise ValidationError("ไฟล์ไม่มีข้อมูล")
        except pd.errors.ParserError as e:
            raise ValidationError(f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์: {str(e)}")


class QuickExamSetupForm(forms.Form):
    """ฟอร์มตั้งค่าการสอบแบบด่วน"""
    subject_name = forms.CharField(
        max_length=100,
        label="ชื่อวิชา",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    student_class = forms.ChoiceField(
        choices=[],
        label="ระดับชั้น",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    exam_date = forms.DateField(
        label="วันที่สอบ",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    duration_hours = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=2,
        label="ระยะเวลาสอบ (ชั่วโมง)",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    auto_assign_all = forms.BooleanField(
        required=False,
        initial=True,
        label="จัดการทั้งหมดอัตโนมัติ",
        help_text="ระบบจะจัดครูและห้องสอบอัตโนมัติ",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classes = StudentProfile.objects.values_list('student_class', flat=True).distinct().order_by('student_class')
        self.fields['student_class'].choices = [("", "เลือกระดับชั้น")] + [(c, c) for c in classes if c]


# ==============================================================================
# ฟอร์มอาคาร/ห้องสอบ และการจัดสรร
# ==============================================================================

class BuildingForm(forms.ModelForm):
    """ฟอร์มเพิ่ม/แก้ไขอาคาร"""
    class Meta:
        model = Building
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'code': 'รหัสอาคาร',
            'name': 'ชื่อโรงเรียน',
            'description': 'รายละเอียด',
        }


class ExamRoomForm(forms.ModelForm):
    """ฟอร์มเพิ่ม/แก้ไขห้องสอบ"""
    class Meta:
        model = ExamRoom
        fields = ['building', 'name', 'capacity']
        widgets = {
            'building': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'เช่น 101, 201'}),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '200',
                'placeholder': 'จำนวนที่นั่ง'
            }),
        }
        labels = {
            'building': 'อาคาร',
            'name': 'ชื่อห้อง',
            'capacity': 'ความจุ (คน)',
        }

    def clean_capacity(self):
        capacity = self.cleaned_data.get('capacity')
        if capacity and capacity <= 0:
            raise ValidationError('ความจุต้องมากกว่า 0')
        return capacity


class RoomBuildingSelectionForm(forms.Form):
    """ฟอร์มสำหรับเลือกอาคารและห้องสอบ (ช่วยกรอง)"""
    building = forms.ModelChoiceField(
        queryset=Building.objects.all(),
        empty_label="เลือกอาคาร",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
            'onchange': 'loadAvailableRooms()'
        }),
        label='อาคาร'
    )
    room = forms.ModelChoiceField(
        queryset=ExamRoom.objects.none(),
        empty_label="เลือกห้องสอบ",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
        }),
        label='ห้องสอบ'
    )

    def __init__(self, *args, **kwargs):
        building_id = kwargs.pop('building_id', None)
        exam_date = kwargs.pop('exam_date', None)
        start_time = kwargs.pop('start_time', None)
        end_time = kwargs.pop('end_time', None)
        super().__init__(*args, **kwargs)

        if building_id:
            rooms = ExamRoom.objects.filter(building_id=building_id, is_active=True)
            if all([exam_date, start_time, end_time]):
                busy = ExamSubject.objects.filter(
                    exam_date=exam_date,
                    start_time__lt=end_time,
                    end_time__gt=start_time
                ).values_list('room_id', flat=True)
                rooms = rooms.exclude(id__in=busy)
            self.fields['room'].queryset = rooms.order_by('name')


class AutoAssignmentForm(forms.Form):
    """ฟอร์มสำหรับการจัดครูและห้องอัตโนมัติ"""
    assignment_type = forms.ChoiceField(
        choices=[
            ('both', 'จัดครูและห้องสอบ'),
            ('teachers', 'จัดครูเท่านั้น'),
            ('rooms', 'จัดห้องสอบเท่านั้น')
        ],
        initial='both',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='ประเภทการจัด'
    )
    prefer_same_building = forms.BooleanField(
        label="ให้ความสำคัญห้องในอาคารเดียวกัน",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    min_teacher_gap_hours = forms.IntegerField(
        label="ช่วงห่างขั้นต่ำระหว่างการคุมสอบ (ชั่วโมง)",
        initial=2,
        min_value=0,
        max_value=8,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class ManualRoomAssignmentForm(forms.Form):
    """ฟอร์มสำหรับเลือกห้องสอบแบบ manual"""
    def __init__(self, *args, **kwargs):
        available_rooms = kwargs.pop('available_rooms', ExamRoom.objects.none())
        super().__init__(*args, **kwargs)

        room_choices = [('', 'เลือกห้องสอบ')]
        for room in available_rooms:
            room_choices.append((
                room.id,
                f"{room.building.name} ห้อง {room.name} (จุ {room.capacity} คน)"
            ))

        self.fields['room'] = forms.ChoiceField(
            choices=room_choices,
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=True,
            label="ห้องสอบ"
        )


class ManualTeacherAssignmentForm(forms.Form):
    """ฟอร์มสำหรับเลือกครูคุมสอบแบบ manual"""
    def __init__(self, *args, **kwargs):
        available_teachers = kwargs.pop('available_teachers', TeacherProfile.objects.none())
        super().__init__(*args, **kwargs)

        teacher_choices = [('', 'เลือกครูคุมสอบ')]
        for t in available_teachers:
            teacher_choices.append((t.id, f"{t.user.get_full_name()} ({t.teacher_id})"))

        self.fields['invigilator'] = forms.ChoiceField(
            choices=teacher_choices,
            label="ครูคุมสอบหลัก",
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=True
        )
        self.fields['secondary_invigilator'] = forms.ChoiceField(
            choices=[('', 'ไม่ระบุครูคุมสอบสำรอง')] + teacher_choices[1:],
            label="ครูคุมสอบสำรอง",
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=False
        )


# ==============================================================================
# ฟอร์มงานหน้างาน - การเช็คชื่อ/ทุจริต
# ==============================================================================

class AttendanceForm(forms.ModelForm):
    """ฟอร์มสำหรับบันทึกการเข้าสอบ"""
    class Meta:
        model = Attendance
        fields = ['status', 'note']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'note': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'หมายเหตุเพิ่มเติม (ถ้ามี)'
            }),
        }
        labels = {
            'status': 'สถานะ',
            'note': 'หมายเหตุ',
        }

class BulkAttendanceForm(forms.Form):
    """ฟอร์มสำหรับบันทึกการเข้าสอบแบบหลายคนพร้อมกัน"""
    student_ids = forms.CharField(widget=forms.HiddenInput())

    bulk_status = forms.ChoiceField(
        choices=Attendance.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none'
        }),
        label='สถานะการเข้าสอบ'
    )
    bulk_note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl focus:border-blue-500 focus:outline-none',
            'rows': 3,
            'placeholder': 'หมายเหตุสำหรับนักเรียนทุกคน'
        }),
        label='หมายเหตุ'
    )

    def clean_student_ids(self):
        raw = self.cleaned_data.get('student_ids')
        if not raw:
            raise ValidationError('กรุณาเลือกนักเรียนอย่างน้อย 1 คน')
        try:
            ids = [int(x) for x in raw.split(',') if x.strip()]
            if not ids:
                raise ValidationError('ข้อมูล ID นักเรียนไม่ถูกต้อง')
            return ids
        except ValueError:
            raise ValidationError('ข้อมูล ID นักเรียนไม่ถูกต้อง')


# ==============================================================================
# ฟอร์มช่วยเหลืออื่น ๆ
# ==============================================================================

class TeacherAssignmentForm(forms.Form):
    """ฟอร์มสำหรับจัดครูแบบเลือกเอง (แสดงครูที่ว่าง)"""
    exam_date = forms.DateField(
        label="วันที่สอบ",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        label="เวลาเริ่มสอบ",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        label="เวลาสิ้นสุดสอบ",
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['available_teachers'] = forms.ModelMultipleChoiceField(
            queryset=TeacherProfile.objects.none(),
            widget=forms.CheckboxSelectMultiple,
            label="ครูที่ว่าง",
            required=False
        )
 
    def set_available_teachers(self, qs):
        self.fields['available_teachers'].queryset = qs