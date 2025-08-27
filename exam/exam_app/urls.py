from django.urls import path
from . import views

urlpatterns = [
    # ========================= หน้าหลักและ Authentication =========================
    path("", views.index_view, name="index_view"),
    path("login/", views.login_user, name="login_user"),
    path("logout/", views.logout_user, name="logout_user"),

    # ========================= Dashboards =========================
    path("admin/", views.dashboard_admin, name="dashboard_admin"),
    path("staff/", views.dashboard_staff, name="dashboard_staff"),
    path("teacher/", views.dashboard_teacher, name="dashboard_teacher"),
    path("student/", views.dashboard_student, name="dashboard_student"),

    # ========================= การจัดการผู้ใช้ (Admin) =========================
    path("admin/users/", views.manage_users, name="manage_users"),
    path("users/list/", views.user_list, name="user_list"),

    # ========================= การจัดการรายวิชาสอบ =========================
    path("exams/", views.exam_subjects, name="exam_subjects"),
    path("exams/add/", views.add_exam_subject, name="add_exam_subject"),
    path("exams/<int:pk>/edit/", views.edit_exam_subject, name="edit_exam_subject"),
    path("exams/<int:pk>/delete/", views.delete_exam_subject, name="delete_exam_subject"),

    path('exam-subjects/enhanced/', views.exam_subjects_enhanced, name='exam_subjects_enhanced'),
    path('exam-subjects/<int:subject_id>/edit/', views.edit_exam_subject_ajax, name='edit_exam_subject_ajax'),
    path('exam-subjects/<int:subject_id>/delete/', views.delete_exam_subject_ajax, name='delete_exam_subject_ajax'),
    path('exam-subjects/bulk-delete/', views.bulk_delete_exam_subjects, name='bulk_delete_exam_subjects'),
    path('exam-subjects/<int:subject_id>/detail/', views.get_exam_subject_detail, name='get_exam_subject_detail'),
    path('exam-subjects/statistics/', views.get_exam_statistics, name='get_exam_statistics'),
    path('exam-subjects/export/', views.export_exam_subjects, name='export_exam_subjects'),

    # ========================= หน้าฟังก์ชันระหว่างสอบ =========================
    path("exams/<int:pk>/attendance/", views.exam_attendance, name="exam_attendance"),
    path("exams/<int:pk>/seating/", views.exam_seating_view, name="exam_seating_view"),
    path('exams/<int:pk>/bulk-attendance/', views.bulk_attendance_update, name='bulk_attendance_update'),

    # ========================= การจัดการห้องสอบ/อาคาร =========================
    path("rooms/", views.manage_rooms, name="manage_rooms"),
    path("rooms/add-building/", views.add_building, name="add_building"),
    path("rooms/add-room/", views.add_room, name="add_room"),

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
    # path("export/subjects/", views.export_subjects_data, name="export_subjects_data"),

    # เทมเพลตดาวน์โหลดไฟล์ตัวอย่าง
    path("download/template/<str:template_type>/", views.download_template, name="download_template"),
    path("download/template/subject/", views.download_subject_template, name="download_subject_template"),


    # ========================= AJAX: การจัดการผู้ใช้ =========================
    path("ajax/user-detail/<str:user_type>/<int:user_id>/", views.ajax_user_detail, name="ajax_user_detail"),
    path("ajax/search-users/", views.ajax_search_users, name="ajax_search_users"),
    path("ajax/class-students-count/", views.get_class_students_count, name="get_class_students_count"),

    # ========================= AJAX: อาคาร/ห้อง =========================
    path("ajax/buildings/", views.get_buildings_data, name="get_buildings_data"),
    path("ajax/buildings/add/", views.add_building_ajax, name="add_building_ajax"),
    path("ajax/buildings/<int:building_id>/edit/", views.edit_building_ajax, name="edit_building_ajax"),
    path("ajax/buildings/<int:building_id>/delete/", views.delete_building_ajax, name="delete_building_ajax"),

    path("ajax/rooms/", views.get_rooms_by_building, name="get_rooms_by_building"),
    path("ajax/rooms/add/", views.add_room_ajax, name="add_room_ajax"),
    path("ajax/rooms/<int:room_id>/edit/", views.edit_room_ajax, name="edit_room_ajax"),
    path("ajax/rooms/<int:room_id>/delete/", views.delete_room_ajax, name="delete_room_ajax"),
    path("ajax/rooms/statistics/", views.get_room_statistics, name="get_room_statistics"),

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

    # ========================= AJAX: เช็คชื่อ =========================
    path("ajax/manual-checkin/", views.manual_checkin, name="manual_checkin"),
    path("ajax/manual-attendance-update/",views.manual_checkin,name="manual_attendance_update"),

    # ========================= AJAX: การจัดการห้องสอบสำหรับ manual selection =========================
    path("ajax/rooms/", views.get_rooms_by_building, name="get_rooms_by_building"),

    # ========================= AJAX: ตรวจสอบความเหมาะสมของห้อง =========================
    path("ajax/check-room-suitability/", views.check_room_suitability, name="check_room_suitability"),
]
