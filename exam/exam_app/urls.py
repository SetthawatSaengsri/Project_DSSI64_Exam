

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
    
    # Admin paths
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('verify_staff/', views.verify_staff_registration, name='verify_staff_registration'),
    path('verify_staff/<int:staff_id>/', views.verify_staff_registration_action, name='verify_staff_registration_action'),
    path('cancel_staff_registration/<int:staff_id>/', views.cancel_staff_registration, name='cancel_staff_registration'),
    path('manage_users/', views.manage_users, name='manage_users'),
    path('manage_users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('manage_users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # Student paths
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    path('exam_schedule/', views.exam_schedule, name='exam_schedule'),
    path('exam_history/', views.exam_history, name='exam_history'),
    path('update_profile/', views.update_profile, name='update_profile'),
    
    # Teacher paths
    path('dashboard/teacher/', views.dashboard_teacher, name='dashboard_teacher'),
    path('exam_subjects_teacher/', views.exam_subjects_teacher, name='exam_subjects_teacher'),
    path('teacher_check_student/', views.teacher_check_student, name='teacher_check_student'),
    path("exam/confirm_exam_entry_teacher/", views.confirm_exam_entry_teacher, name="confirm_exam_entry_teacher"),
    path("manual_teacher_checkin/", views.manual_teacher_checkin, name="manual_teacher_checkin"),
    
    # Staff paths 
    path('dashboard_staff/', views.dashboard_staff, name='dashboard_staff'),
    path('import_csv/', views.import_csv, name='import_csv'),
    path('import_exam_subjects/', views.import_exam_subjects_csv, name='import_exam_subjects_csv'),
    path('staff/school_members/', views.school_members, name='school_members'),
    path('add_exam_subject/', views.add_exam_subject, name='add_exam_subject'),
    path('exam_subjects_staff/', views.exam_subjects_staff, name='exam_subjects_staff'),
    path('edit_exam_subject/<int:subject_id>/', views.edit_exam_subject, name='edit_exam_subject'),
    path('delete_exam_subject/<int:subject_id>/', views.delete_exam_subject, name='delete_exam_subject'),
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
