#models.py

from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    school_name = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['username', 'school_name'], name='unique_username_per_school')
        ]

    def __str__(self):
        return self.email


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    student_id = models.CharField(max_length=10)
    no_student = models.CharField(max_length=10)
    student_class = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student_id', 'user'], name='unique_student_per_user')
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
    id_card = models.FileField(upload_to='id_cards/', null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Building(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.code})"

class ExamRoom(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms', null=True)
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('building', 'name')

    def __str__(self):
        building_name = self.building.name if self.building else "ไม่ระบุอาคาร"
        return f"{building_name} ห้อง {self.name} (จุ {self.capacity} คน)"

class ExamSubject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=5)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    school_name = models.CharField(max_length=100, null=True, blank=True)

    TERM_CHOICES = [
        ("1", "เทอม 1"),
        ("2", "เทอม 2"),
        ("3", "เทอม 3"),
    ]
    term = models.CharField(max_length=1, choices=TERM_CHOICES, default="1")

    room = models.ForeignKey(
        ExamRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ห้องสอบ"
    )

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
    invigilator_checkin_time = models.DateTimeField(null=True, blank=True)
    secondary_invigilator_checkin = models.BooleanField(default=False)
    secondary_invigilator_checkin_time = models.DateTimeField(null=True, blank=True)

    qr_expiration = models.TimeField(null=True, blank=True, help_text="เวลาที่ QR Code หมดอายุ")

    students = models.ManyToManyField(
        StudentProfile,
        blank=True,
        related_name='exam_subjects',
        verbose_name="นักเรียน"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject_code', 'school_name', 'academic_year', 'term'],
                name='unique_subject_per_school_year_term'
            )
        ]

    def __str__(self):
        room_name = self.room.room_name if self.room else "ไม่ระบุห้อง"
        return f"{self.subject_name} ({self.subject_code}) ห้อง {room_name}"


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

