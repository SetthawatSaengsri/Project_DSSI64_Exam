# models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from uuid import uuid4

class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    student_id = models.CharField(max_length=10, unique=True)
    no_student = models.CharField(max_length=10)
    CLASS_CHOICES = [
        ('1/1', '1/1'),
        ('1/2', '1/2'),
        ('2/1', '2/1'),
        ('2/2', '2/2'),
        ('3/1', '3/1'),
        ('3/2', '3/2'),
        ('4/1', '4/1'),
        ('4/2', '4/2'),
        ('5/1', '5/1'),
        ('5/2', '5/2'),
        ('6/1', '6/1'),
        ('6/2', '6/2'),
    ]
    student_class = models.CharField(max_length=10, choices=CLASS_CHOICES, default='1/1')

    def __str__(self):
        return self.student_class
    
class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

class ExamRoom(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    
    def __str__(self):
        return f"{self.name} (Capacity: {self.capacity})"
    
class ExamSubject(models.Model):
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=10)
    academic_year = models.CharField(max_length=4)
    student_class = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='exam_subjects_class')
    exam_room = models.ForeignKey(ExamRoom, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    invigilator = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='invigilated_exams')
    subject_teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, related_name='taught_subjects')
    students = models.ManyToManyField(StudentProfile, related_name='registered_exams', blank=True)

    def __str__(self):
        return f"{self.subject_name} ({self.academic_year})"

class QRToken(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='qr_tokens')
    token = models.CharField(max_length=36, default=uuid4, unique=True)
    expiry_time = models.DateTimeField()

    def __str__(self):
        return f"Token for {self.student.user.username} expires {self.expiry_time}"

    def is_valid(self):
        return timezone.now() < self.expiry_time

class SeatAssignment(models.Model):
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='seat_assignments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='seat_assignments')
    seat_number = models.CharField(max_length=10)

    class Meta:
        unique_together = ('exam_subject', 'student')

    def __str__(self):
        return f"Seat {self.seat_number} for {self.student.user.username} in {self.exam_subject.subject_name}"
    
class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    student_class = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='news_items')
