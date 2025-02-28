from django.urls import path
from . import views

urlpatterns = [

    path('', views.index_view, name='index_view'),  

    # Register and login URLs
    path('register_staff/', views.register_staff, name='register_staff'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path("exam_completed/", views.exam_completed, name="exam_completed"),
    path("update_attendance_status/", views.update_attendance_status, name="update_attendance_status"),
    path("scanner/teacher/", views.scanner, name="scanner"),
    

    # Student paths
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    
    # Teacher paths
    path('dashboard/teacher/', views.dashboard_teacher, name='dashboard_teacher'),
    path('exam_subjects_teacher/', views.exam_subjects_teacher, name='exam_subjects_teacher'),
    path('teacher_check_student/', views.teacher_check_student, name='teacher_check_student'),
    path("exam/confirm_exam_entry_teacher/", views.confirm_exam_entry_teacher, name="confirm_exam_entry_teacher"),
    
    # Staff paths
    path('dashboard_staff/', views.dashboard_staff, name='dashboard_staff'),
    path('import_csv/', views.import_csv, name='import_csv'),
    path('staff/school_members/', views.school_members, name='school_members'),
    path('add_exam_subject/', views.add_exam_subject, name='add_exam_subject'),
    path('exam_subjects_staff/', views.exam_subjects_staff, name='exam_subjects_staff'),
    path('edit_exam_subject/<int:subject_id>/', views.edit_exam_subject, name='edit_exam_subject'),
    path('delete_exam_subject/<int:subject_id>/', views.delete_exam_subject, name='delete_exam_subject'),
    path('statistics_view/', views.statistics_view, name='statistics_view'),
    path('select_exam_subject/', views.select_exam_subject, name='select_exam_subject'),
    path('exam_detail/<int:subject_id>/', views.exam_detail, name='exam_detail'),


    # QR code generation paths
    path('exam/confirm_exam_entry/', views.confirm_exam_entry, name='confirm_exam_entry'),
    path('exam_subjects/qr/<int:subject_id>/', views.generate_qr_code, name='generate_qr_code'),
    path("confirm_exam_checkin/", views.confirm_exam_checkin, name="confirm_exam_checkin"),

    # Exam attendance status and manual check-in
    path('exam/select_subject/', views.select_exam_subject, name='select_exam_subject'),
    path('exam/<int:subject_id>/attendance/', views.exam_attendance_status, name='exam_attendance_status'),
    path("manual_checkin/", views.manual_checkin, name="manual_checkin"),
    path("teacher_checkin/", views.teacher_checkin, name="teacher_checkin"),
]
