from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib import messages
from .models import *


# Custom UserAdmin for managing all user types
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher', 'is_staff', 'school_name')
    list_filter = ('is_student', 'is_teacher', 'is_staff', 'school_name')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'school_name')

admin.site.register(User, CustomUserAdmin)

# ✅ ฟังก์ชันลบนักเรียนทั้งหมด
def delete_all_students(modeladmin, request, queryset):
    student_users = User.objects.filter(is_student=True)
    student_profiles = StudentProfile.objects.all()

    # ลบ StudentProfile ทั้งหมด
    student_profiles.delete()
    # ลบ User ที่เป็นนักเรียนทั้งหมด
    student_users.delete()

    messages.success(request, "✅ ลบนักเรียนทั้งหมดเรียบร้อยแล้ว!")

delete_all_students.short_description = "🗑️ ลบนักเรียนทั้งหมด"

# StudentProfile admin with detailed view
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'no_student', 'student_class', 'get_user_email']
    search_fields = ['user__username', 'student_id', 'no_student']
    list_filter = ['student_class']
    actions = [delete_all_students]  # ✅ เพิ่ม action สำหรับลบนักเรียนทั้งหมด

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

# TeacherProfile admin with detailed view
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'teacher_id', 'get_user_email']
    search_fields = ['user__username', 'teacher_id']
    list_filter = ['user__is_staff']

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

# StaffProfile admin
@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'school_name', 'get_user_email']
    search_fields = ['user__username', 'school_name']
    list_filter = ['school_name']

    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'

# เพิ่มการจัดการ ExamSubject ในหน้า Admin
@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'subject_code', 'academic_year', 'exam_date', 'start_time', 'end_time', 'room', 'invigilator']
    search_fields = ['subject_name', 'subject_code', 'academic_year', 'room', 'invigilator__user__username']
    list_filter = ['academic_year', 'exam_date', 'invigilator']
    filter_horizontal = ['students']  # ให้มีตัวเลือกหลายคนในฟิลด์นักเรียน

    def get_invigilator(self, obj):
        return obj.invigilator.user.username if obj.invigilator else "ไม่มีผู้คุมสอบ"
    get_invigilator.short_description = 'ผู้คุมสอบ'

# เพิ่มการจัดการ Attendance ในหน้า Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'status', 'checkin_time']
    list_filter = ['status', 'subject']
    search_fields = ['student__user__username', 'subject__subject_name']
    list_select_related = ['student', 'subject']

    def get_checkin_time(self, obj):
        return obj.checkin_time.strftime("%Y-%m-%d %H:%M") if obj.checkin_time else "ยังไม่ได้เช็คชื่อ"
    get_checkin_time.short_description = 'เวลาเช็คชื่อ'
