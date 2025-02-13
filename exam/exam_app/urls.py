from django.urls import path
from . import views

urlpatterns = [

    path('', views.index_view, name='index_view'),  

    # Register and login URLs
    path('register_staff/', views.register_staff, name='register_staff'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),

    # Student paths
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),
    path('edit_student/student/', views.edit_student, name='edit_student'),
    path('Examination_history/student/', views.Examination_history, name='Examination_history'),

    # Teacher paths
    path('scanner/teacher/', views.scanner, name='scanner'),
    path('dashboard/teacher/', views.dashboard_teacher, name='dashboard_teacher'),
    path('exam_subjects_teacher/', views.exam_subjects_teacher, name='exam_subjects_teacher'),

    # Staff paths
    path('dashboard_staff/', views.dashboard_staff, name='dashboard_staff'),
    path('import_csv/', views.import_csv, name='import_csv'),
    path('staff/school_members/', views.school_members, name='school_members'),
    path('add_exam_subject/', views.add_exam_subject, name='add_exam_subject'),
    path('exam_subjects_staff/', views.exam_subjects_staff, name='exam_subjects_staff'),
    path('edit_exam_subject/<int:subject_id>/', views.edit_exam_subject, name='edit_exam_subject'),
    path('delete_exam_subject/<int:subject_id>/', views.delete_exam_subject, name='delete_exam_subject'),

    # QR code generation paths
    path('exam_subjects/qr/<int:subject_id>/', views.generate_qr_code, name='generate_qr_code'),

    # Scanning and confirmation of exam entry
    path('scan_qr_checkin/', views.scan_qr_checkin, name='scan_qr_checkin'),
    path('exam/confirm_exam_entry/', views.confirm_exam_entry, name='confirm_exam_entry'),

    # Exam attendance status and manual check-in
    path('exam/select_subject/', views.select_exam_subject, name='select_exam_subject'),
    path('exam/<int:subject_id>/attendance/', views.exam_attendance_status, name='exam_attendance_status'),
    path("manual_checkin/", views.manual_checkin, name="manual_checkin"),
    path("teacher_checkin/", views.teacher_checkin, name="teacher_checkin"),
]
