from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *


class CustomUserAdmin(UserAdmin):
    """การจัดการผู้ใช้งานใน Admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_teacher', 'is_student', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('บทบาทเพิ่มเติม', {
            'fields': ('is_student', 'is_teacher')
        }),
    )
    
    def get_role(self, obj):
        return obj.get_role()
    get_role.short_description = 'บทบาท'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """การจัดการโปรไฟล์นักเรียน"""
    list_display = ('student_id', 'get_full_name', 'student_class', 'student_number', 'is_active', 'created_at')
    list_filter = ('student_class', 'user__is_active', 'created_at')
    search_fields = ('student_id', 'user__first_name', 'user__last_name', 'user__email', 'student_class')
    ordering = ('student_class', 'student_number')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ชื่อ-สกุล'
    
    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True
    is_active.short_description = 'สถานะใช้งาน'


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    """การจัดการโปรไฟล์ครู"""
    list_display = ('teacher_id', 'get_full_name', 'department', 'is_active', 'created_at')
    list_filter = ('department', 'user__is_active', 'created_at')
    search_fields = ('teacher_id', 'user__first_name', 'user__last_name', 'user__email', 'department')
    ordering = ('user__first_name',)
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ชื่อ-สกุล'
    
    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True
    is_active.short_description = 'สถานะใช้งาน'


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    """การจัดการโปรไฟล์เจ้าหน้าที่"""
    list_display = ('staff_id', 'get_full_name', 'position', 'department', 'is_active', 'created_at')
    list_filter = ('position', 'department', 'user__is_active', 'created_at')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name', 'user__email', 'position')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ชื่อ-สกุล'
    
    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True
    is_active.short_description = 'สถานะใช้งาน'


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """การจัดการอาคาร"""
    list_display = ('code', 'name', 'get_room_count', 'get_total_capacity', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('code', 'name', 'description')
    ordering = ('code',)
    
    def get_room_count(self, obj):
        return obj.get_room_count()
    get_room_count.short_description = 'จำนวนห้อง'
    
    def get_total_capacity(self, obj):
        return f"{obj.get_total_capacity():,} คน"
    get_total_capacity.short_description = 'ความจุรวม'


@admin.register(ExamRoom)
class ExamRoomAdmin(admin.ModelAdmin):
    """การจัดการห้องสอบ - ลบฟิลด์โปรเจคเตอร์และแอร์"""
    list_display = ('get_full_name', 'building', 'capacity', 'is_active', 'created_at')
    list_filter = ('building', 'is_active', 'created_at')
    search_fields = ('name', 'building__name', 'building__code')
    ordering = ('building__code', 'name')
    
    def get_full_name(self, obj):
        # ไม่พึ่งพาเมธอดในโมเดล
        return f"{obj.building.name} ห้อง {obj.name}"


@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    """การจัดการรายวิชาสอบ"""
    list_display = ('subject_name', 'subject_code', 'academic_year', 'term', 'exam_date', 'get_room_info', 'get_teacher_info', 'get_student_count', 'is_active')
    list_filter = ('academic_year', 'term', 'exam_date', 'is_active', 'created_at')
    search_fields = ('subject_name', 'subject_code', 'room__name', 'invigilator__user__first_name')
    ordering = ('-exam_date', 'start_time')
    filter_horizontal = ('students',)
    
    def get_room_info(self, obj):
        if obj.room:
            return f"{obj.room.get_full_name()} (จุ {obj.room.capacity} คน)"
        return "ไม่ระบุห้อง"
    get_room_info.short_description = 'ห้องสอบ'
    
    def get_teacher_info(self, obj):
        teachers = []
        if obj.invigilator:
            teachers.append(f"หลัก: {obj.invigilator.user.get_full_name()}")
        if obj.secondary_invigilator:
            teachers.append(f"สำรอง: {obj.secondary_invigilator.user.get_full_name()}")
        return " | ".join(teachers) if teachers else "ไม่ระบุครู"
    get_teacher_info.short_description = 'ครูคุมสอบ'
    
    def get_student_count(self, obj):
        return f"{obj.get_student_count()} คน"
    get_student_count.short_description = 'จำนวนนักเรียน'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """การจัดการการเข้าสอบ - เพิ่มสถานะทุจริต"""
    list_display = ('get_student_info', 'get_subject_info', 'status', 'checkin_time', 'get_late_info', 'recorded_by', 'created_at')
    list_filter = ('status', 'subject__exam_date', 'subject__academic_year', 'created_at')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name', 'subject__subject_name')
    ordering = ('-created_at',)
    
    def get_student_info(self, obj):
        return f"{obj.student.student_id} - {obj.student.user.get_full_name()}"
    get_student_info.short_description = 'นักเรียน'
    
    def get_subject_info(self, obj):
        return f"{obj.subject.subject_name} ({obj.subject.exam_date})"
    get_subject_info.short_description = 'วิชาสอบ'
    
    def get_late_info(self, obj):
        if obj.status == 'late' and obj.is_late():
            return f"สาย {obj.get_minutes_late()} นาที"
        elif obj.status == 'cheating':
            return format_html('<span style="color: red; font-weight: bold;">⚠️ ทุจริต</span>')
        return "-"
    get_late_info.short_description = 'รายละเอียด'


@admin.register(CheatingReport)
class CheatingReportAdmin(admin.ModelAdmin):
    """การจัดการรายงานทุจริต"""
    list_display = ('get_student_info', 'get_subject_info', 'cheating_type', 'status', 'reported_by', 'get_days_since_report', 'created_at')
    list_filter = ('cheating_type', 'status', 'created_at', 'attendance__subject__academic_year')
    search_fields = ('attendance__student__student_id', 'attendance__student__user__first_name', 'attendance__subject__subject_name', 'reported_by__first_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'get_days_since_report')
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('attendance', 'reported_by', 'cheating_type', 'status')
        }),
        ('รายละเอียดการทุจริต', {
            'fields': ('description', 'action_taken', 'witness', 'evidence_files')
        }),
        ('การติดตาม', {
            'fields': ('investigation_notes', 'final_decision', 'penalty', 'resolved_by', 'resolved_at')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_student_info(self, obj):
        return f"{obj.attendance.student.student_id} - {obj.attendance.student.user.get_full_name()}"
    get_student_info.short_description = 'นักเรียน'
    
    def get_subject_info(self, obj):
        return f"{obj.attendance.subject.subject_name}"
    get_subject_info.short_description = 'วิชา'
    
    def get_days_since_report(self, obj):
        days = obj.get_days_since_report()
        if days == 0:
            return "วันนี้"
        elif days == 1:
            return "เมื่อวาน"
        else:
            return f"{days} วันที่แล้ว"
    get_days_since_report.short_description = 'ระยะเวลาตั้งแต่รายงาน'


@admin.register(CheatingStatistics)
class CheatingStatisticsAdmin(admin.ModelAdmin):
    """การจัดการสถิติการทุจริต"""
    list_display = ('year', 'month', 'total_cases', 'resolved_cases', 'confirmed_cases', 'dismissed_cases', 'get_resolution_rate', 'get_confirmation_rate')
    list_filter = ('year', 'month')
    ordering = ('-year', '-month')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_resolution_rate(self, obj):
        rate = obj.get_resolution_rate()
        color = "green" if rate >= 80 else "orange" if rate >= 60 else "red"
        return format_html(f'<span style="color: {color}; font-weight: bold;">{rate}%</span>')
    get_resolution_rate.short_description = 'อัตราการดำเนินการ'
    
    def get_confirmation_rate(self, obj):
        rate = obj.get_confirmation_rate()
        return f"{rate}%"
    get_confirmation_rate.short_description = 'อัตราการยืนยันทุจริต'


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    """การจัดการเซสชันการสอบ"""
    list_display = ('get_subject_info', 'total_students', 'present_students', 'absent_students', 'get_attendance_rate', 'started_at', 'ended_at')
    list_filter = ('subject__exam_date', 'subject__academic_year', 'created_at')
    search_fields = ('subject__subject_name', 'subject__subject_code')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_subject_info(self, obj):
        return f"{obj.subject.subject_name} ({obj.subject.exam_date})"
    get_subject_info.short_description = 'วิชาสอบ'
    
    def get_attendance_rate(self, obj):
        rate = obj.get_attendance_rate()
        color = "green" if rate >= 90 else "orange" if rate >= 75 else "red"
        return format_html(f'<span style="color: {color}; font-weight: bold;">{rate:.1f}%</span>')
    get_attendance_rate.short_description = 'อัตราการเข้าสอบ'


# ลงทะเบียน Admin
# ตรวจสอบและลงทะเบียน CustomUserAdmin
if User in admin.site._registry:
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ปรับแต่งหน้า Admin
admin.site.site_header = "ระบบจัดการการสอบ"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "จัดการระบบสอบออนไลน์"