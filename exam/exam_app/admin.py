# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, News, ExamSubject, ExamRoom

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher', *UserAdmin.list_display)
    list_filter = ('is_student', 'is_teacher', *UserAdmin.list_filter)

    def is_student(self, obj):
        return obj.student_profile.exists()
    is_student.boolean = True
    is_student.short_description = 'Is student?'

    def is_teacher(self, obj):
        return obj.teacher_profile.exists()
    is_teacher.boolean = True
    is_teacher.short_description = 'Is teacher?'

admin.site.register(User, CustomUserAdmin)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [ 'user', 'student_id', 'get_first_name', 'get_last_name','no_student', 'student_class']
    search_fields = ['user__username', 'student_id', 'no_student']
    list_filter = ['student_class']

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.admin_order_field = 'user__first_name'  
    get_first_name.short_description = 'First Name'  

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.admin_order_field = 'user__last_name'  
    get_last_name.short_description = 'Last Name'  

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user','teacher_id']
    search_fields = ['user__username', 'teacher_id']


# กำหนดค่าการแสดงผลของ ExamSubject ใน Django Admin
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'subject_code', 'academic_year', 'get_student_class', 'exam_room', 'start_time', 'end_time', 'get_invigilator', 'get_subject_teacher')

    def get_student_class(self, obj):
        return obj.student_class.student_class
    get_student_class.short_description = 'Student Class'

    def get_invigilator(self, obj):
        return obj.invigilator.user.username if obj.invigilator else '-'
    get_invigilator.short_description = 'Invigilator'

    def get_subject_teacher(self, obj):
        return obj.subject_teacher.user.username if obj.subject_teacher else '-'
    get_subject_teacher.short_description = 'Subject Teacher'

# ลงทะเบียน ExamSubject พร้อมกับการตั้งค่า Custom Admin
admin.site.register(ExamSubject, ExamSubjectAdmin)

# Register other models as needed
admin.site.register(News)
admin.site.register(ExamRoom)
