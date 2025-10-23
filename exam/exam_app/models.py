from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class User(AbstractUser):
    """ผู้ใช้งานระบบ - ขยายจาก AbstractUser"""
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=False, verbose_name="นักเรียน")
    is_teacher = models.BooleanField(default=False, verbose_name="ครู")
    is_staff = models.BooleanField(default=False, verbose_name="เจ้าหน้าที่")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "ผู้ใช้งาน"

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_role(self):
        """ดึงบทบาทของผู้ใช้"""
        if self.is_superuser:
            return "ผู้ดูแลระบบ"
        elif self.is_teacher:
            return "ครู"
        elif self.is_student:
            return "นักเรียน"
        elif self.is_staff:
            return "เจ้าหน้าที่"
        return "ผู้ใช้ทั่วไป"


class StudentProfile(models.Model):
    """โปรไฟล์นักเรียน"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True, verbose_name="รหัสนักเรียน")
    student_number = models.CharField(max_length=10, verbose_name="เลขที่")  # เปลี่ยนเป็น CharField
    student_class = models.CharField(max_length=20, verbose_name="ระดับชั้น")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    
    class Meta:
        verbose_name = "โปรไฟล์นักเรียน"
        verbose_name_plural = "โปรไฟล์นักเรียน"
        unique_together = ['student_class', 'student_number']
        ordering = ['student_class', 'student_number']

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()} ({self.student_class})"


class TeacherProfile(models.Model):
    """โปรไฟล์ครู"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    teacher_id = models.CharField(max_length=20, unique=True, verbose_name="รหัสครู")
    department = models.CharField(max_length=100, blank=True, verbose_name="แผนก/กลุ่มสาระ")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    
    class Meta:
        verbose_name = "โปรไฟล์ครู"
        verbose_name_plural = "โปรไฟล์ครู"
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return f"{self.teacher_id} - {self.user.get_full_name()}"


class StaffProfile(models.Model):
    """โปรไฟล์เจ้าหน้าที่"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    staff_id = models.CharField(max_length=20, unique=True, blank=True, verbose_name="รหัสเจ้าหน้าที่")
    position = models.CharField(max_length=50, default='เจ้าหน้าที่', verbose_name="ตำแหน่ง")
    department = models.CharField(max_length=100, blank=True, verbose_name="แผนก")
    id_card = models.FileField(upload_to='staff_documents/', null=True, blank=True, verbose_name="เอกสารประกอบ")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    
    class Meta:
        verbose_name = "โปรไฟล์เจ้าหน้าที่"
        verbose_name_plural = "โปรไฟล์เจ้าหน้าที่"

    def __str__(self):
        return f"{self.staff_id} - {self.user.get_full_name()} ({self.position})"


class Building(models.Model):
    """อาคาร"""
    code = models.CharField(max_length=10, unique=True, verbose_name="รหัสอาคาร")
    name = models.CharField(max_length=100, verbose_name="ชื่ออาคาร")
    description = models.TextField(blank=True, verbose_name="รายละเอียด")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    
    class Meta:
        verbose_name = "อาคาร"
        verbose_name_plural = "อาคาร"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_total_capacity(self):
        """ความจุรวมของอาคาร"""
        return self.rooms.aggregate(
            total=models.Sum('capacity')
        )['total'] or 0

    def get_room_count(self):
        """จำนวนห้องทั้งหมด"""
        return self.rooms.count()


class ExamRoom(models.Model):
    """ห้องสอบ"""
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms', verbose_name="อาคาร")
    name = models.CharField(max_length=50, verbose_name="ชื่อห้อง")
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(200)],
        verbose_name="ความจุ"
    )
    is_active = models.BooleanField(default=True, verbose_name="ใช้งานได้")
    notes = models.TextField(blank=True, verbose_name="หมายเหตุ")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    class Meta:
        verbose_name = "ห้องสอบ"
        verbose_name_plural = "ห้องสอบ"
        unique_together = ('building', 'name')
        ordering = ['building__code', 'name']

    def __str__(self):
        return f"{self.building.name} ห้อง {self.name} (จุ {self.capacity} คน)"

    def get_full_name(self):
        """ชื่อเต็มของห้อง"""
        return f"{self.building.name} ห้อง {self.name}"


class ExamSubject(models.Model):
    """รายวิชาสอบ"""
    TERM_CHOICES = [
        ("1", "เทอม 1"),
        ("2", "เทอม 2"), 
        ("3", "เทอม 3"),
    ]
    
    subject_name = models.CharField(max_length=200, verbose_name="ชื่อวิชา")
    subject_code = models.CharField(max_length=20, verbose_name="รหัสวิชา")
    academic_year = models.CharField(max_length=10, verbose_name="ปีการศึกษา")
    term = models.CharField(max_length=1, choices=TERM_CHOICES, default="1", verbose_name="ภาคเรียน")
    
    exam_date = models.DateField(verbose_name="วันสอบ")
    start_time = models.TimeField(verbose_name="เวลาเริ่มสอบ")
    end_time = models.TimeField(verbose_name="เวลาสิ้นสุดสอบ")
    
    room = models.ForeignKey(
        ExamRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exam_subjects',
        verbose_name="ห้องสอบ"
    )
    
    invigilator = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_exam_subjects',
        verbose_name="ครูคุมสอบหลัก"
    )
    
    secondary_invigilator = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='secondary_exam_subjects',
        verbose_name="ครูคุมสอบสำรอง"
    )
    
    # สถานะการเช็คชื่อของครู
    invigilator_checkin = models.BooleanField(default=False, verbose_name="ครูหลักเช็คชื่อแล้ว")
    invigilator_checkin_time = models.DateTimeField(null=True, blank=True, verbose_name="เวลาเช็คชื่อครูหลัก")
    secondary_invigilator_checkin = models.BooleanField(default=False, verbose_name="ครูสำรองเช็คชื่อแล้ว")
    secondary_invigilator_checkin_time = models.DateTimeField(null=True, blank=True, verbose_name="เวลาเช็คชื่อครูสำรอง")
    
    students = models.ManyToManyField(
        StudentProfile,
        blank=True,
        related_name='exam_subjects',
        verbose_name="นักเรียน"
    )
    
    # ข้อมูลเพิ่มเติม
    instructions = models.TextField(blank=True, verbose_name="คำแนะนำพิเศษ")
    is_active = models.BooleanField(default=True, verbose_name="เปิดใช้งาน")
    
    # ข้อมูลการสร้าง
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="สร้างโดย")
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")
    
    class Meta:
        verbose_name = "รายวิชาสอบ"
        verbose_name_plural = "รายวิชาสอบ"
        constraints = [
            models.UniqueConstraint(
                fields=['subject_code', 'academic_year', 'term'],
                name='unique_subject_per_year_term'
            )
        ]
        ordering = ['exam_date', 'start_time']

    def __str__(self):
        room_name = f"ห้อง {self.room.get_full_name()}" if self.room else "ไม่ระบุห้อง"
        return f"{self.subject_name} ({self.subject_code}) - {room_name}"
    
    def get_duration(self):
        """ระยะเวลาสอบ (นาที)"""
        start_datetime = datetime.combine(timezone.now().date(), self.start_time)
        end_datetime = datetime.combine(timezone.now().date(), self.end_time)
        duration = end_datetime - start_datetime
        return int(duration.total_seconds() / 60)

    def get_student_count(self):
        """จำนวนนักเรียนที่สอบ"""
        return self.students.count()
    
    def is_upcoming(self):
        """ตรวจสอบว่าการสอบจะมาถึงหรือไม่"""
        exam_datetime = datetime.combine(self.exam_date, self.start_time)
        exam_datetime = timezone.make_aware(exam_datetime)
        return exam_datetime > timezone.now()
    
    def is_ongoing(self):
        """ตรวจสอบว่าการสอบกำลังดำเนินการอยู่หรือไม่"""
        now = timezone.now()
        exam_start = datetime.combine(self.exam_date, self.start_time)
        exam_end = datetime.combine(self.exam_date, self.end_time)
        exam_start = timezone.make_aware(exam_start)
        exam_end = timezone.make_aware(exam_end)
        return exam_start <= now <= exam_end
    
    def is_finished(self):
        """ตรวจสอบว่าการสอบสิ้นสุดแล้วหรือไม่"""
        exam_end = datetime.combine(self.exam_date, self.end_time)
        exam_end = timezone.make_aware(exam_end)
        return exam_end < timezone.now()
    
    def get_status(self):
        """สถานะการสอบ"""
        if self.is_finished():
            return "สิ้นสุดแล้ว"
        elif self.is_ongoing():
            return "กำลังสอบ"
        elif self.is_upcoming():
            return "จะมาถึง"
        return "ไม่ทราบสถานะ"
    
    def can_checkin(self):
        """ตรวจสอบว่าสามารถเช็คชื่อได้หรือไม่ (ก่อนเวลาสอบ 30 นาที)"""
        exam_start = datetime.combine(self.exam_date, self.start_time)
        exam_start = timezone.make_aware(exam_start)
        checkin_start = exam_start - timedelta(minutes=30)
        now = timezone.now()
        return checkin_start <= now <= exam_start

    @property
    def student_count(self):
        """จำนวนนักเรียนที่ลงทะเบียน - Property สำหรับ compatibility"""
        return self.get_student_count()
    
    @property
    def attendance_summary(self):
        """สรุปการเข้าสอบ"""
        total = self.get_student_count()
        present = self.attendances.filter(status__in=['on_time', 'late']).count()
        absent = total - present
        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': round((present/total*100) if total > 0 else 0, 1)
        }


class Attendance(models.Model):
    """การเข้าสอบ"""
    STATUS_CHOICES = [
        ("on_time", "มาตรงเวลา"),
        ("late", "มาสาย"),
        ("absent", "ขาดสอบ"),
        ("excused", "ลาป่วย/ลากิจ"),
        ("cheating", "ทุจริต"), 
    ]

    student = models.ForeignKey(
        StudentProfile, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name="นักเรียน"
    )
    subject = models.ForeignKey(
        ExamSubject, 
        on_delete=models.CASCADE, 
        related_name='attendances',
        verbose_name="รายวิชา"
    )
    checkin_time = models.DateTimeField(null=True, blank=True, verbose_name="เวลาเช็คชื่อ")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="absent", verbose_name="สถานะ")
    note = models.TextField(blank=True, verbose_name="หมายเหตุ")
    
    # ข้อมูลการบันทึก
    recorded_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="บันทึกโดย"
    )
    
    # ฟิลด์วันที่ - แก้ไขให้รองรับข้อมูลเก่า
    created_at = models.DateTimeField(null=True, blank=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")
    
    class Meta:
        verbose_name = "การเข้าสอบ"
        verbose_name_plural = "การเข้าสอบ"
        unique_together = ('student', 'subject')
        ordering = ['-checkin_time']

    def save(self, *args, **kwargs):
        # ตั้งค่า created_at ถ้ายังไม่มี
        if not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.subject.subject_name} ({self.get_status_display()})"

    def is_late(self):
        """ตรวจสอบว่ามาสายหรือไม่"""
        if not self.checkin_time:
            return False
        
        exam_start = datetime.combine(self.subject.exam_date, self.subject.start_time)
        exam_start = timezone.make_aware(exam_start)
        return self.checkin_time > exam_start
    
    def get_minutes_late(self):
        """จำนวนนาทีที่มาสาย"""
        if not self.is_late() or not self.checkin_time:
            return 0
        
        exam_start = datetime.combine(self.subject.exam_date, self.subject.start_time)
        exam_start = timezone.make_aware(exam_start)
        late_duration = self.checkin_time - exam_start
        return int(late_duration.total_seconds() / 60)


class ExamSession(models.Model):
    """เซสชันการสอบ (สำหรับเก็บข้อมูลการดำเนินการสอบ)"""
    subject = models.OneToOneField(
        ExamSubject, 
        on_delete=models.CASCADE, 
        related_name='session',
        verbose_name="วิชาสอบ"
    )
    
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="เริ่มสอบเมื่อ")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="จบสอบเมื่อ")
    
    total_students = models.PositiveIntegerField(default=0, verbose_name="จำนวนนักเรียนทั้งหมด")
    present_students = models.PositiveIntegerField(default=0, verbose_name="จำนวนนักเรียนที่มา")
    absent_students = models.PositiveIntegerField(default=0, verbose_name="จำนวนนักเรียนที่ขาด")
    
    notes = models.TextField(blank=True, verbose_name="หมายเหตุการสอบ")
    
    created_at = models.DateTimeField(default=timezone.now, editable=False, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    class Meta:
        verbose_name = "เซสชันการสอบ"
        verbose_name_plural = "เซสชันการสอบ"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"เซสชัน {self.subject.subject_name} - {self.subject.exam_date}"
    
    def get_attendance_rate(self):
        """คำนวดอัตราการเข้าสอบ"""
        if self.total_students == 0:
            return 0
        return (self.present_students / self.total_students) * 100
    
    def update_statistics(self):
        """อัพเดทสถิติการเข้าสอบ"""
        self.total_students = self.subject.get_student_count()
        
        attendances = self.subject.attendances.all()
        self.present_students = attendances.exclude(status='absent').count()
        self.absent_students = attendances.filter(status='absent').count()
        
        self.save()


# ==================== SIGNALS FOR AUTO-UPDATE ====================
@receiver(post_save, sender=Attendance)
def update_exam_session_on_attendance_save(sender, instance, **kwargs):
    """อัพเดทเซสชันเมื่อมีการบันทึกการเข้าสอบ"""
    try:
        session, created = ExamSession.objects.get_or_create(subject=instance.subject)
        session.update_statistics()
    except Exception as e:
        print(f"Error updating exam session: {str(e)}")

@receiver(post_delete, sender=Attendance)
def update_exam_session_on_attendance_delete(sender, instance, **kwargs):
    """อัพเดทเซสชันเมื่อมีการลบการเข้าสอบ"""
    try:
        session = ExamSession.objects.get(subject=instance.subject)
        session.update_statistics()
    except ExamSession.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error updating exam session: {str(e)}")

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """สร้างโปรไฟล์อัตโนมัติเมื่อสร้างผู้ใช้ใหม่"""
    if created:
        # โปรไฟล์จะต้องสร้างด้วยตนเองเพราะมีฟิลด์ที่จำเป็น
        # เช่น student_id, teacher_id เป็นต้น
        pass


# ==================== CUSTOM MANAGERS ====================
class ActiveExamSubjectManager(models.Manager):
    """Manager สำหรับ ExamSubject ที่ยังใช้งานได้"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class UpcomingExamSubjectManager(models.Manager):
    """Manager สำหรับ ExamSubject ที่จะมาถึง"""
    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(
            exam_date__gte=now.date(),
            is_active=True
        ).order_by('exam_date', 'start_time')

# เพิ่ม managers ให้กับ ExamSubject
ExamSubject.add_to_class('objects', models.Manager())
ExamSubject.add_to_class('active', ActiveExamSubjectManager())
ExamSubject.add_to_class('upcoming', UpcomingExamSubjectManager())