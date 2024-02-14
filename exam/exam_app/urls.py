# urls.py
from django.urls import path
from .views import *
from . import views


# class ClassSlugConverter:
#     regex = '[^/]+'

#     def to_python(self, value):
#         return value.replace('_', '/')

#     def to_url(self, value):
#         return value.replace('/', '_')

# register_converter(ClassSlugConverter, 'class_slug')


urlpatterns = [

    path('', views.index_view, name='index_view'),  
    path('register_student/', views.register_student, name='register_student'),
    path('register_teacher/', views.register_teacher, name='register_teacher'),
    path('success_page/', views.success_page, name='success_page'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('dashboard/unknown/',views.dashboard_unknown, name='dashboard_unknown'),

    #student
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    path('edit_student/student/',views.edit_student, name='edit_student'),
    path('Examination_history/student/',views.Examination_history, name='Examination_history'),
    path('student/<int:student_id>/qr/', views.generate_qr_for_student, name='generate_qr_for_student'),

    #teacher
    path('dashboard/teacher/',views.dashboard_teacher, name='dashboard_teacher'),
    path('add_exam_subject/', add_exam_subject, name='add_exam_subject'),
    path('exam_subject_list/', exam_subject_list, name='exam_subject_list'),
    path('exam_subject/edit/<int:subject_id>/', edit_exam_subject, name='edit_exam_subject'),
    path('exam_subject/update/', views.update_exam_subject, name='update_exam_subject'),
    path('exam_subject/delete/<int:subject_id>/', views.delete_exam_subject, name='delete_exam_subject'),
    path('class/<slug:class_slug>/', class_students_list, name='class_students_list'),
    
]
