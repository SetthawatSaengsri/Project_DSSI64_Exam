# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, TeacherProfile, StaffProfile


# Custom UserAdmin for managing all user types
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher', 'is_staff', 'school_name')
    list_filter = ('is_student', 'is_teacher', 'is_staff', 'school_name')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'school_name')


admin.site.register(User, CustomUserAdmin)


# StudentProfile admin with detailed view
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'no_student', 'student_class', 'get_user_email']
    search_fields = ['user__username', 'student_id', 'no_student']
    list_filter = ['student_class']

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



