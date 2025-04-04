#models.py

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
   

class User(AbstractUser):
    username = models.CharField(max_length=150)  # อนุญาตให้ username ซ้ำได้
    email = models.EmailField(unique=True)  # Email ยังคงไม่สามารถซ้ำได้
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    school_name = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'  # ใช้ email เป็นตัวระบุตัวตนหลัก
    REQUIRED_FIELDS = ['username']  # username ยังเป็น requiredำ

    class Meta:
        constraints = [
            # อนุญาต username ซ้ำได้ในโรงเรียนที่ต่างกัน
            models.UniqueConstraint(fields=['username', 'school_name'], name='unique_username_per_school')
        ]

    def __str__(self):
        return self.email



class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    student_id = models.CharField(max_length=10)  # ลบ unique=True
    no_student = models.CharField(max_length=10)
    student_class = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student_id', 'user'], name='unique_student_per_user') # กำหนดให้ student_id ซ้ำไม่ได้ในโรงเรียนเดียวกัน
        ]

    def __str__(self):
        return self.student_class

    
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=10)  
    school_name = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['teacher_id', 'school_name'], name='unique_teacher_per_school') 
        ]

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    school_name = models.CharField(max_length=100)
    id_card = models.FileField(upload_to='id_cards/', null=True, blank=True)  # บันทึกไฟล์ที่อัพโหลด

    def __str__(self):
        return f"Profile for {self.user.username}"
    
class ExamSubject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=4)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    school_name = models.CharField(max_length=100, null=True, blank=True)
    room = models.CharField(max_length=20, blank=True, verbose_name="ห้องสอบ")
    secondary_invigilator_checkin = models.BooleanField(default=False)
    qr_expiration = models.TimeField(null=True, blank=True, help_text="เวลาที่ QR Code หมดอายุ (ตัวอย่าง: 14:30)")  # เพิ่มฟิลด์นี้
    
    invigilator = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invigilated_exams',
        verbose_name="ผู้คุมสอบหลัก"
    )
    secondary_invigilator = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secondary_invigilated_exams',
        verbose_name="ผู้คุมสอบสำรอง"
    )
    invigilator_checkin = models.BooleanField(default=False)
    students = models.ManyToManyField(
        StudentProfile,
        blank=True,
        related_name='exam_subjects',
        verbose_name="นักเรียน"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject_code', 'school_name'], 
                name='unique_subject_code_per_school'
            )
        ]

    def __str__(self):
        return f"{self.subject_name} ({self.subject_code})"



class Attendance(models.Model):
    STATUS_CHOICES = [
        ("on_time", "มาตรงเวลา"),
        ("late", "มาสาย"),
        ("absent", "ขาดสอบ"),
    ]

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    checkin_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="absent")

    def __str__(self):
        return f"{self.student.user.first_name} - {self.subject.subject_name} ({self.status})"

