from django.urls import path
from . import views

urlpatterns = [
    # ========================= หน้าหลักและ Authentication =========================
    path("", views.index_view, name="index_view"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),

    path("qr/scan/", views.qr_scanner, name="qr_scanner"),
    # ========================= Dashboards =========================
    # Dashboard APIs
    path('staff/', views.dashboard_staff, name='dashboard_staff'),
    path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
    path('api/dashboard-stats/', views.dashboard_staff_stats, name='dashboard_staff_stats'),
    path('api/academic-years/', views.get_academic_years_api, name='get_academic_years_api'),
    path('api/exam-statistics/', views.exam_statistics_api, name='exam_statistics_api'),

    path("teacher/", views.dashboard_teacher, name="dashboard_teacher"),
    path("exams/invigilated/", views.invigilated_subjects, name="invigilated_subjects"),
    path('api/teacher-dashboard-data/', views.teacher_dashboard_data_api, name='teacher_dashboard_data_api'),
    path('api/teacher-class-list/', views.get_teacher_class_list_api, name='teacher_class_list_api'),
    path('api/teacher-academic-years/', views.get_teacher_academic_years_api,name='get_teacher_academic_years_api'),

    # ========================= Student Dashboard APIs =========================
    path("student/", views.dashboard_student, name="dashboard_student"),
    path('api/student-dashboard-data/', views.student_dashboard_data_api, name='student_dashboard_data_api'),
    path('api/student-academic-years/', views.get_student_academic_years_api, name='get_student_academic_years_api'),
    path('api/student-exam-detail/<int:exam_id>/', views.student_exam_detail_api, name='student_exam_detail_api'),
    path('api/student-attendance-history/', views.student_attendance_history_api, name='student_attendance_history_api'),
    path("student/exam-schedule/", views.student_exam_schedule, name="student_exam_schedule"),
    
    # ========================= การจัดการผู้ใช้ (Admin) =========================
    path("admin/users/", views.manage_users, name="manage_users"),
    path("users/list/", views.user_list, name="user_list"),
    path('api/user-detail/<str:user_type>/<int:user_id>/', views.user_detail_api, name='user_detail_api'),
    path('api/update-user/<str:user_type>/<int:user_id>/', views.update_user_api, name='update_user_api'),

    # ========================= การจัดการรายวิชาสอบ =========================
    path("exams/", views.exam_subjects, name="exam_subjects"),
    path("exams/add/", views.add_exam_subject, name="add_exam_subject"),
    path("exams/<int:pk>/edit/", views.edit_exam_subject, name="edit_exam_subject"),
    path("exams/<int:pk>/delete/", views.delete_exam_subject, name="delete_exam_subject"),

    # Enhanced exam subjects management
    path('exam-subjects/bulk-delete/', views.bulk_delete_exam_subjects, name='bulk_delete_exam_subjects'),
    path('exam-subjects/<int:subject_id>/detail/', views.get_exam_subject_detail, name='get_exam_subject_detail'),
    path('exam-subjects/statistics/', views.get_exam_statistics, name='get_exam_statistics'),
    path('exam-subjects/export/', views.export_exam_subjects, name='export_exam_subjects'),

    # ========================= AJAX Endpoints สำหรับแก้ไข/ลบ =========================
    path('ajax/exam-subjects/<int:subject_id>/edit/', views.edit_exam_subject_ajax, name='edit_exam_subject_ajax'),
    path('ajax/exam-subjects/<int:subject_id>/delete/', views.delete_exam_subject_ajax, name='delete_exam_subject_ajax'),
    path('ajax/get-available-teachers-for-edit/', views.get_available_teachers_for_edit, name='get_available_teachers_for_edit'),
    path('ajax/get-available-rooms-for-edit/', views.get_available_rooms_for_edit, name='get_available_rooms_for_edit'),
    path('ajax/get-class-list/', views.get_class_list, name='get_class_list'),
    path('exam-subjects/force-delete/', views.force_delete_exam_subjects, name='force_delete_exam_subjects'),
    
    # ========================= หน้าฟังก์ชันระหว่างสอบ =========================
    path("exams/<int:pk>/attendance/", views.exam_attendance, name="exam_attendance"),
    path("exams/<int:pk>/seating/", views.exam_seating_view, name="exam_seating_view"),
    path('exams/<int:pk>/bulk-attendance/', views.bulk_attendance_update, name='bulk_attendance_update'),
    

    # ========================= Seating Chart & Real-time Updates =========================
    path('exams/<int:subject_id>/seating/', views.exam_seating_view, name='exam_seating_view'),
    path('exams/<int:subject_id>/seating-data/', views.exam_seating_data, name='exam_seating_data'),

    # ========================= Manual Check-in =========================  
    path('ajax/manual-checkin-student/', views.manual_checkin_student, name='manual_checkin_student'),

    # ========================= ระบบ QR/Check-in (alias ไปหน้าเช็คชื่อ) =========================
    path('checkin/<int:pk>/', views.checkin_exam, name='checkin_exam'),
    path("exams/<int:pk>/qr/", views.generate_qr_code, name="generate_qr_code"),

    # ========================= ฟังก์ชัน Import/Export =========================
    path("import/students/", views.import_students, name="import_students"),
    path("import/teachers/", views.import_teachers, name="import_teachers"),
    path("import/subjects/", views.import_exam_subjects, name="import_exam_subjects"),
    
    path("export/users/<str:user_type>/", views.export_users, name="export_users"),
    path("export/rooms/", views.export_rooms_data, name="export_rooms_data"),

    # เทมเพลตดาวน์โหลดไฟล์ตัวอย่าง
    path("download/template/<str:template_type>/", views.download_template, name="download_template"),
    path("download/template/subject/", views.download_subject_template, name="download_subject_template"),

    # ========================= AJAX: การจัดการผู้ใช้ =========================
    path("ajax/user-detail/<str:user_type>/<int:user_id>/", views.ajax_user_detail, name="ajax_user_detail"),
    path("ajax/search-users/", views.ajax_search_users, name="ajax_search_users"),
    path("ajax/class-students-count/", views.get_class_students_count, name="get_class_students_count"),

    # ========================= AJAX: อาคาร/ห้อง =========================
    # ========================= การจัดการห้องสอบ =========================

    path("rooms/", views.manage_rooms, name="manage_rooms"),
    path("ajax/buildings/", views.get_buildings_data, name="get_buildings_data"),
    path("ajax/buildings/add/", views.add_building_ajax, name="add_building_ajax"),
    path("ajax/buildings/<int:building_id>/edit/", views.edit_building_ajax, name="edit_building_ajax"),
    path("ajax/buildings/<int:building_id>/delete/", views.delete_building_ajax, name="delete_building_ajax"),
    path("ajax/rooms/add/", views.add_room_ajax, name="add_room_ajax"),
    path("ajax/rooms/<int:room_id>/edit/", views.edit_room_ajax, name="edit_room_ajax"),
    path("ajax/rooms/<int:room_id>/delete/", views.delete_room_ajax, name="delete_room_ajax"),
    path("ajax/rooms/statistics/", views.get_room_statistics, name="get_room_statistics"),
    
    path("ajax/rooms/", views.get_rooms_by_building, name="get_rooms_by_building"),
    path("ajax/teachers/add/", views.ajax_teachers_add, name="ajax_teachers_add"),

    # ========================= AJAX: รายวิชาสอบ/ทรัพยากร =========================
    path("ajax/check-teacher-conflicts/", views.check_teacher_conflicts, name="check_teacher_conflicts"),
    path("ajax/get-available-teachers/", views.get_available_teachers, name="get_available_teachers"),
    path("ajax/check-room-availability/", views.check_room_availability, name="check_room_availability"),

    path("ajax/auto-assign-room/", views.auto_assign_room, name="auto_assign_room"),
    path("ajax/auto-assign-teachers/", views.auto_assign_teachers, name="auto_assign_teachers"),
    path("ajax/bulk-auto-assign/", views.bulk_auto_assign, name="bulk_auto_assign"),

    path("ajax/assign-room-manual/<int:subject_id>/", views.assign_room_manual, name="assign_room_manual"),
    path("ajax/assign-teachers-manual/<int:subject_id>/", views.assign_teachers_manual, name="assign_teachers_manual"),
    path("ajax/get-available-resources/", views.get_available_resources_for_manual_assignment, name="get_available_resources_for_manual_assignment"),
    
    path('api/server-time/', views.get_server_time, name='server_time'),

    # ========================= AJAX: เช็คชื่อ =========================
    path("ajax/manual-checkin/", views.manual_checkin, name="manual_checkin"),
    path("ajax/manual-attendance-update/", views.manual_checkin, name="manual_attendance_update"),
    path('ajax/exam-stats/<int:subject_id>/', views.get_exam_stats, name='get_exam_stats'),
    path('export/attendance/<int:subject_id>/', views.export_attendance_report, name='export_attendance_report'),
    path('ajax/teacher-checkin/', views.teacher_manual_checkin, name='teacher_manual_checkin'),

    # ========================= AJAX: ตรวจสอบความเหมาะสมของห้อง =========================
    path("ajax/check-room-suitability/", views.check_room_suitability, name="check_room_suitability"),
    
    
]