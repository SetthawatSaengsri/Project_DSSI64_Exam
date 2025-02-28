#views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse,HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.contrib import messages
from .forms import *
from .models import * 
import json
import qrcode
from io import BytesIO
import base64
from django.contrib.auth.decorators import user_passes_test
import csv
import pandas as pd
import pytz
from datetime import datetime
import qrcode
from django.utils.timezone import localtime ,now
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta 
import qrcode.image.pil
from django.db.models import Count


def index_view(request):
    schools = StaffProfile.objects.values_list('school_name', flat=True).distinct()
    return render(request, 'app/index.html', {'schools': schools})

def login_user(request):
    schools = StaffProfile.objects.values_list('school_name', flat=True).distinct()

    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        school_name = request.POST.get('school_name')

        try:
            user = User.objects.get(email=email, school_name=school_name)
        except User.DoesNotExist:
            user = None

        if user and user.check_password(password):
            login(request, user)
            if user.is_student:
                return redirect('dashboard_student')
            elif user.is_teacher:
                return redirect('dashboard_teacher')
            elif user.is_staff:
                return redirect('dashboard_staff')
            else:
                return redirect('index_view')
        else:
            messages.error(request, 'ข้อมูลการเข้าสู่ระบบไม่ถูกต้อง')

    return render(request, 'app/index.html', {'schools': schools})

@login_required
def scanner(request):
    return render(request, 'app/teacher/scanner.html')

@login_required
def logout_user(request):
    logout(request)
    return redirect('index_view')

def is_staff_user(user):
    return user.is_staff

def register_staff(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff registration successful.')
            return redirect('dashboard_staff')
    else:
        form = StaffRegistrationForm()
    return render(request, 'app/register_staff.html', {'form': form})

@login_required
def dashboard_staff(request):
    school_name = request.user.school_name
    subjects = ExamSubject.objects.filter(invigilator__school_name=school_name).order_by('exam_date')

    teacher_count = TeacherProfile.objects.filter(user__school_name=school_name).count()
    student_count = StudentProfile.objects.filter(user__school_name=school_name).count()
    subject_count = ExamSubject.objects.filter(invigilator__school_name=school_name).count()

    return render(request, 'app/staff/dashboard_staff.html', {
        'subjects': subjects,
        'teacher_count': teacher_count,
        'student_count': student_count,
        'subject_count': subject_count
    })

def statistics_view(request):
    school_name = request.user.school_name

    # ✅ นับจำนวนครู, นักเรียน และรายวิชาในโรงเรียน
    teacher_count = TeacherProfile.objects.filter(user__school_name=school_name).count()
    student_count = StudentProfile.objects.filter(user__school_name=school_name).count()
    subject_count = ExamSubject.objects.filter(invigilator__school_name=school_name).count()

    # ✅ ดึงระดับชั้นทั้งหมด
    class_list = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()

    # ✅ ข้อมูลรวมของโรงเรียน
    attendance_data = {
        "all": {
            "on_time": 0,
            "late": 0,
            "absent": 0,
            "total_students": student_count,
            "total_teachers": teacher_count,
            "total_subjects": subject_count
        }
    }

    # ✅ ตรวจสอบข้อมูลของแต่ละระดับชั้น
    for class_name in class_list:
        students = StudentProfile.objects.filter(student_class=class_name, user__school_name=school_name)
        student_ids = students.values_list('id', flat=True)

        # ✅ ถ้าไม่มีนักเรียนในระดับชั้นนี้ ให้ตั้งค่าเป็น 0
        attendance_data[class_name] = {
            "on_time": 0,
            "late": 0,
            "absent": 0,
            "total_students": students.count(),
            "total_subjects": ExamSubject.objects.filter(students__student_class=class_name).distinct().count(),
            "total_teachers": teacher_count
        }

        # ✅ นับจำนวนสถานะการเข้าสอบ
        records = Attendance.objects.filter(student_id__in=student_ids).values("status").annotate(count=Count("id"))

        for record in records:
            status_key = record["status"]

            # ตรวจสอบว่า status_key เป็น tuple หรือไม่ และแยกค่าที่ถูกต้อง
            if isinstance(status_key, tuple):
                status_key = status_key[0]  # ใช้แค่สถานะหลัก เช่น 'late' หรือ 'on_time'

            # เพิ่มข้อมูลการนับสถานะ
            if status_key in attendance_data[class_name]:
                attendance_data[class_name][status_key] += record["count"]
            else:
                attendance_data[class_name][status_key] = record["count"]

            # นับข้อมูลรวม
            if status_key in attendance_data["all"]:
                attendance_data["all"][status_key] += record["count"]
            else:
                attendance_data["all"][status_key] = record["count"]

    # ✅ ถ้าไม่มีข้อมูล ให้ตั้งค่าเริ่มต้นเป็น 0 เพื่อป้องกันกราฟว่าง
    for key in attendance_data:
        if "on_time" not in attendance_data[key]:
            attendance_data[key]["on_time"] = 0
        if "late" not in attendance_data[key]:
            attendance_data[key]["late"] = 0
        if "absent" not in attendance_data[key]:
            attendance_data[key]["absent"] = 0

    # ✅ ส่งข้อมูลไปยังเทมเพลต
    return render(request, "app/staff/statistics.html", {
        "teacher_count": teacher_count,
        "student_count": student_count,
        "subject_count": subject_count,
        "class_list": class_list,
        "attendance_data": attendance_data
    })

    
def import_csv(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        role = request.POST.get('role')

        if not file:
            messages.error(request, 'กรุณาเลือกไฟล์เพื่ออัปโหลด')
            return redirect('import_csv')

        try:
            data = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)

            for _, row in data.iterrows():
                username = row['Username']
                email = row['Email']
                school_name = request.user.school_name

                # ตรวจสอบว่ามี email ซ้ำหรือไม่
                if User.objects.filter(email=email).exists():
                    messages.warning(request, f"อีเมล {email} มีอยู่แล้ว")
                    continue

                # ตรวจสอบ username และ school_name ซ้ำกันหรือไม่
                if User.objects.filter(username=username, school_name=school_name).exists():
                    messages.warning(request, f"ชื่อผู้ใช้ {username} มีอยู่แล้วในโรงเรียน {school_name}")
                    continue

                # สร้างผู้ใช้ใหม่
                user = User.objects.create_user(
                    username=username,
                    first_name=row['First Name'],
                    last_name=row['Last Name'],
                    email=email,
                    password=row['Password'],
                    is_student=(role == 'student'),
                    is_teacher=(role == 'teacher'),
                    school_name=school_name
                )

                if role == 'student':
                    StudentProfile.objects.create(
                        user=user,
                        student_id=row['Student ID'],
                        no_student=row.get('No Student', ''),
                        student_class=row['Student Class']
                    )
                elif role == 'teacher':
                    # ตรวจสอบ teacher_id ซ้ำในโรงเรียน
                    if TeacherProfile.objects.filter(teacher_id=row['Teacher ID'], school_name=school_name).exists():
                        messages.warning(request, f"รหัสครู {row['Teacher ID']} มีอยู่แล้วในโรงเรียน {school_name}")
                        continue

                    TeacherProfile.objects.create(
                        user=user,
                        teacher_id=row['Teacher ID'],
                        school_name=school_name
                    )

            messages.success(request, 'ข้อมูลนำเข้าเสร็จสมบูรณ์')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {e}')

    return render(request, 'app/staff/import_csv.html')


@login_required
def school_members(request):
    if not request.user.is_staff:
        return HttpResponse("คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้", status=403)

    school_name = request.user.school_name
    students = StudentProfile.objects.filter(user__school_name=school_name).select_related('user').order_by('student_class', 'user__last_name')
    teachers = TeacherProfile.objects.filter(user__school_name=school_name).select_related('user').order_by('user__last_name')

    students_by_class = {}
    for student in students:
        student_class = student.student_class if student.student_class else "ไม่ระบุ"
        if student_class not in students_by_class:
            students_by_class[student_class] = []
        students_by_class[student_class].append(student)

    return render(request, 'app/staff/school_members.html', {
        'school_name': school_name,
        'students_by_class': students_by_class,
        'teachers': teachers
    })

from django.utils import timezone
thai_tz = pytz.timezone('Asia/Bangkok')

@login_required
def add_exam_subject(request):
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, user=request.user)
        if form.is_valid():
            subject = form.save(commit=False)

            # แปลงเวลาให้เป็นเวลาไทย
            thai_tz = pytz.timezone('Asia/Bangkok')
            subject.start_time = timezone.make_aware(form.cleaned_data['start_time'], timezone=thai_tz)
            subject.end_time = timezone.make_aware(form.cleaned_data['end_time'], timezone=thai_tz)

            # ดึงนักเรียนที่อยู่ในระดับชั้นที่เลือก
            selected_class = form.cleaned_data['student_class']
            students = StudentProfile.objects.filter(
                student_class=selected_class, 
                user__school_name=request.user.school_name
            )

            # บันทึกข้อมูล
            subject.save()
            subject.students.set(students)  # เพิ่มนักเรียนที่มีระดับชั้นนี้เข้าไป
            subject.save()

            messages.success(request, f"เพิ่มรายวิชา {subject.subject_name} สำเร็จ!")
            return redirect('exam_subjects_staff')
        else:
            messages.error(request, "ข้อมูลไม่ถูกต้อง กรุณากรอกข้อมูลให้ครบถ้วน")
            print("ฟอร์มมีข้อผิดพลาด:", form.errors)
    else:
        form = ExamSubjectForm(user=request.user)

    return render(request, 'app/staff/add_exam_subject.html', {'form': form})


@login_required
def exam_subjects_staff(request):
    if not request.user.is_staff:
        return HttpResponse("คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้", status=403)

    school_name = request.user.school_name
    subjects = ExamSubject.objects.filter(invigilator__school_name=school_name).select_related('invigilator')

    # ✅ ดึงระดับชั้นทั้งหมด
    classes = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()

    selected_class = request.GET.get('student_class', 'all')

    if selected_class != 'all' and selected_class:
        subjects = subjects.filter(students__student_class=selected_class).distinct()

    # ✅ เพิ่มระดับชั้นให้แต่ละรายวิชา
    for subject in subjects:
        subject.grades = list(subject.students.values_list('student_class', flat=True).distinct())

    # ✅ Debug log ตรวจสอบข้อมูล
    print("📚 วิชาในระบบ:")
    for sub in subjects:
        print(f"📌 {sub.subject_name}, ระดับชั้นที่เกี่ยวข้อง: {sub.grades}")

    return render(request, 'app/staff/exam_subjects_staff.html', {
        'school_name': school_name,
        'subjects': subjects,
        'classes': classes,
        'selected_class': selected_class,
    })

@login_required
def select_exam_subject(request):
    # ดึงโรงเรียนของผู้ใช้งาน
    school_name = request.user.school_name

    # ดึงข้อมูลวิชาที่ผู้ใช้งานมีสิทธิ์เข้าถึง (กรองตามโรงเรียนของผู้ใช้)
    subjects = ExamSubject.objects.filter(students__user__school_name=school_name).distinct()

    # ดึงระดับชั้นที่มีอยู่ในระบบจากข้อมูลของนักเรียน
    grades = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()

    # เพิ่มระดับชั้นของแต่ละวิชา
    for subject in subjects:
        subject.grades = list(subject.students.values_list('student_class', flat=True).distinct())

    return render(request, 'app/staff/select_exam_subject.html', {
        'subjects': subjects,
        'grades': grades
    })

@login_required
def exam_detail(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)

    teachers = TeacherProfile.objects.filter(invigilated_exams=subject).select_related('user')
    students = StudentProfile.objects.filter(exam_subjects=subject).select_related('user').order_by('student_class', 'user__last_name')

    # Assign seat numbers based on the order
    for idx, student in enumerate(students, start=1):
        student.seat_number = idx  # Assign sequential seat numbers
        student.save()

    # ✅ ดึงข้อมูลการเช็คชื่อ
    attendance_records = Attendance.objects.filter(subject=subject)
    
    # ✅ สร้าง dictionary ที่ใช้ student_id เป็น key
    attendance_dict = {record.student.id: record for record in attendance_records}

    if request.method == "POST":
        student_id = request.POST.get("student_id")
        new_status = request.POST.get("status")

        if student_id and new_status:
            student = get_object_or_404(StudentProfile, id=student_id)
            attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)
            attendance.status = new_status
            attendance.checkin_time = now()
            attendance.save()
            messages.success(request, "อัปเดตสถานะเรียบร้อยแล้ว ✅")
            return redirect('exam_detail', subject_id=subject.id)

    return render(request, 'app/staff/exam_detail.html', {
        'subject': subject,
        'students': students,
        'teachers': teachers,
        'attendance_dict': attendance_dict,  # ✅ ส่ง dictionary ไปยัง template
        'status_choices': ['on_time', 'late', 'absent'],  # เปลี่ยนเป็นค่าที่ใช้งานในฐานข้อมูล
    })



@login_required
def delete_exam_subject(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)
    subject.delete()
    messages.success(request, f"ลบรายวิชา {subject.subject_name} สำเร็จ!")
    return redirect('exam_subjects_staff')

@login_required
def edit_exam_subject(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id, invigilator__school_name=request.user.school_name)
    thai_tz = pytz.timezone('Asia/Bangkok')  # ✅ ตั้งค่าโซนเวลาไทย

    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, instance=subject, user=request.user)
        if form.is_valid():
            subject = form.save(commit=False)

            # ✅ แปลงเวลาเริ่มและเวลาสิ้นสุดเป็นเวลาไทย
            subject.start_time = timezone.make_aware(form.cleaned_data['start_time'], timezone=thai_tz)
            subject.end_time = timezone.make_aware(form.cleaned_data['end_time'], timezone=thai_tz)

            # ✅ อัปเดตนักเรียนตามระดับชั้นที่เลือกใหม่
            selected_class = form.cleaned_data['student_class']
            students = StudentProfile.objects.filter(
                student_class=selected_class,
                user__school_name=request.user.school_name
            )

            subject.save()
            subject.students.set(students)  # ✅ อัปเดตนักเรียนที่อยู่ในระดับชั้นที่เลือก
            subject.save()

            # ✅ Debug Log
            print(f"✅ แก้ไขวิชา: {subject.subject_name}, ระดับชั้นใหม่: {selected_class}, นักเรียน: {list(students.values_list('user__username', flat=True))}")

            messages.success(request, f"✅ แก้ไขรายวิชา {subject.subject_name} สำเร็จ!")
            return redirect('exam_subjects_staff')
        else:
            messages.error(request, "❌ กรุณากรอกข้อมูลให้ถูกต้อง")
            print("❌ ฟอร์มมีข้อผิดพลาด:", form.errors)  # ✅ Debug error
    else:
        form = ExamSubjectForm(instance=subject, user=request.user)

    return render(request, 'app/staff/edit_exam_subject.html', {
        'form': form,
        'subject': subject
    })


thai_tz = pytz.timezone('Asia/Bangkok')

@login_required
def generate_qr_code(request, subject_id):
    """ ฟังก์ชันสร้าง QR Code สำหรับยืนยันเข้าสอบ (บังคับให้ล็อกอินก่อนเข้า) """
    subject = get_object_or_404(ExamSubject, id=subject_id)
    qr_url = request.build_absolute_uri(f"/exam/confirm_exam_entry/?subject_id={subject_id}")

    # ✅ รองรับการสร้าง QR Code โดยครูและเจ้าหน้าที่ (student_id ไม่บังคับ)
    if request.user.is_student:
        try:
            student_profile = StudentProfile.objects.get(user=request.user)
            qr_url += f"&student_id={student_profile.id}"
        except StudentProfile.DoesNotExist:
            pass  # ถ้าไม่มี student_id ไม่ต้องเพิ่มเข้าไป
            
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return render(request, "app/staff/qr_code.html", {
        "subject": subject,
        "img_base64": img_base64,
        "qr_url": qr_url
    })
 
@csrf_exempt  
@login_required
def confirm_exam_entry(request):
    if request.method == "GET":
        # รับรหัสวิชาจาก query parameter
        subject_id = request.GET.get("subject_id")
        if not subject_id:
            return JsonResponse({"status": "error", "message": "❌ ไม่พบรหัสวิชา"}, status=400)

        # ดึงข้อมูลของวิชาจากฐานข้อมูล
        subject = get_object_or_404(ExamSubject, id=subject_id)

        student, teacher = None, None
        seat_number = None

        # หากผู้ใช้เป็นนักเรียน ให้ดึงข้อมูลของนักเรียน
        if request.user.is_student:
            student = get_object_or_404(StudentProfile, user=request.user)
            seating = SeatingPlan.objects.filter(student=student, subject=subject).first()
            seat_number = seating.seat_number if seating else "-"

        # หากผู้ใช้เป็นครู ให้ดึงข้อมูลของครู
        elif request.user.is_teacher:
            teacher = get_object_or_404(TeacherProfile, user=request.user)

        # ส่งข้อมูลไปยังหน้า confirm_exam.html
        return render(request, "app/confirm_exam.html", {
            "subject": subject,
            "student": student,
            "teacher": teacher,
            "seat_number": seat_number
        })

    elif request.method == "POST":
        try:
            # รับข้อมูลจาก body ของ request
            data = json.loads(request.body)
            subject_id = data.get("subject_id")

            if not subject_id:
                return JsonResponse({"status": "error", "message": "❌ ไม่มี subject_id"}, status=400)

            # ดึงข้อมูลของวิชาจากฐานข้อมูล
            subject = get_object_or_404(ExamSubject, id=subject_id)

            # หากผู้ใช้เป็นนักเรียน
            if request.user.is_student:
                student = get_object_or_404(StudentProfile, user=request.user)

                # ตรวจสอบว่านักเรียนได้เช็คชื่อหรือยัง
                attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)
                if not created:
                    return JsonResponse({"status": "error", "message": "❌ คุณได้เช็คชื่อไปแล้ว!"}, status=400)

                # บันทึกสถานะเช็คชื่อ
                attendance.status = "on_time"
                attendance.checkin_time = now()
                attendance.save()

            # หากผู้ใช้เป็นครู
            elif request.user.is_teacher:
                teacher = get_object_or_404(TeacherProfile, user=request.user)

                # ตรวจสอบว่าเป็นครูคุมสอบของวิชานี้หรือไม่
                if subject.invigilator != teacher:
                    return JsonResponse({"status": "error", "message": "❌ คุณไม่ใช่ครูคุมสอบวิชานี้"}, status=403)

                # อัปเดตสถานะการเช็คชื่อของครู
                subject.invigilator_checkin = True
                subject.save()

            return JsonResponse({"status": "success", "message": "✅ เช็คชื่อสำเร็จ!"})

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "❌ ข้อมูล JSON ไม่ถูกต้อง"}, status=400)
        except Exception as e:
            # จัดการกรณีอื่น ๆ ที่อาจเกิดข้อผิดพลาด
            return JsonResponse({"status": "error", "message": f"❌ เกิดข้อผิดพลาด: {str(e)}"}, status=500)

    return JsonResponse({"status": "error", "message": "❌ Method Not Allowed"}, status=405)


@login_required
def exam_completed(request):
    """ หน้ายืนยันเสร็จสิ้น """
    return render(request, "app/exam_completed.html")

@csrf_exempt
@login_required
def confirm_exam_checkin(request):
    if request.method == "POST":
        data = json.loads(request.body)
        student_id = data.get("student_id")
        subject_id = data.get("subject_id")

        student = get_object_or_404(StudentProfile, id=student_id)
        subject = get_object_or_404(ExamSubject, id=subject_id)

        if request.user != student.user:
            return JsonResponse({"status": "error", "message": "คุณไม่มีสิทธิ์เช็คชื่อเข้าสอบนี้"}, status=403)

        Attendance.objects.create(student=student, subject=subject, status="on_time")

        return JsonResponse({"status": "success", "message": "เช็คชื่อสำเร็จ!"})

    return JsonResponse({"status": "error", "message": "Method Not Allowed"}, status=405)


@login_required
def exam_attendance_status(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)

    # ✅ ตรวจสอบสิทธิ์
    if request.user.is_staff:
        pass  # Staff ดูได้ทุกวิชา
    elif request.user.is_teacher:
        teacher_profile = getattr(request.user, 'teacher_profile', None)  # ✅ แก้ไขตรงนี้
        if not teacher_profile or subject.invigilator != teacher_profile:
            return HttpResponseForbidden("❌ คุณไม่มีสิทธิ์ดูวิชานี้")
    else:
        return HttpResponseForbidden("❌ คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้")

    # ✅ ดึงนักเรียนที่ลงทะเบียนสอบในวิชานี้
    students = subject.students.all()

    # ✅ ดึงข้อมูลการเช็คชื่อ
    attendance_records = Attendance.objects.filter(subject=subject)
    attendance_dict = {att.student.id: att for att in attendance_records}

    return render(request, 'app/staff/exam_attendance_status.html', {
        'subject': subject,
        'students': students,
        'attendance_dict': attendance_dict,
        'teacher_checked_in': subject.invigilator_checkin  # ✅ แสดงสถานะครูคุมสอบ
    })


@login_required
def update_attendance_status(request):
    """ ตรวจสอบว่านักเรียนขาดสอบหรือมาสายโดยอัตโนมัติ """
    subjects = ExamSubject.objects.all()
    current_time = now()
    attendance_status = {}

    for subject in subjects:
        exam_start_time = subject.start_time
        late_threshold = exam_start_time + timedelta(minutes=30)

        # ดึงนักเรียนที่ยังไม่ได้เช็คชื่อ
        absent_students = Attendance.objects.filter(subject=subject, checkin_time__isnull=True)
        for record in absent_students:
            if current_time > exam_start_time:
                record.status = "absent"
            attendance_status[str(record.student.id)] = record.status

        # ดึงนักเรียนที่มาสาย
        late_students = Attendance.objects.filter(subject=subject, checkin_time__gt=exam_start_time, checkin_time__lte=late_threshold)
        for record in late_students:
            record.status = "late"
            attendance_status[str(record.student.id)] = record.status

        Attendance.objects.bulk_update(absent_students, ['status'])
        Attendance.objects.bulk_update(late_students, ['status'])

    return JsonResponse({"status": "success", "attendance_status": attendance_status})


@csrf_exempt
def manual_checkin(request):
    """ ฟังก์ชันให้เจ้าหน้าที่เลือกสถานะของนักเรียน """
    if request.method == "POST":
        data = json.loads(request.body)
        student_id = data.get("student_id")
        subject_id = data.get("subject_id")
        status = data.get("status")  # รับค่าจาก Modal

        student = get_object_or_404(StudentProfile, id=student_id)
        subject = get_object_or_404(ExamSubject, id=subject_id)

        attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)
        attendance.checkin_time = now()
        attendance.status = status  # อัปเดตสถานะจาก Modal

        # กำหนดสีตามสถานะที่เลือก
        color_map = {
            "on_time": "#16a34a",  # เขียว
            "late": "#facc15",  # เหลือง
            "absent": "#dc2626",  # แดง
        }
        color = color_map.get(status, "#d1d5db")  # Default เป็นสีเทา

        attendance.save()
        return JsonResponse({"status": "success", "color": color})

    return JsonResponse({"status": "error"}, status=400)

@login_required
def dashboard_teacher(request):
    user = request.user

    # ✅ ตรวจสอบว่าผู้ใช้เป็นครูจริง
    try:
        teacher_profile = TeacherProfile.objects.get(user=user)
    except TeacherProfile.DoesNotExist:
        teacher_profile = None

    if not teacher_profile:
        return render(request, 'app/error.html', {'message': 'คุณไม่ได้เป็นครู'})

    # ✅ ดึงจำนวนวิชาที่ครูดูแล
    subjects = ExamSubject.objects.filter(invigilator=teacher_profile)
    subject_count = subjects.count()

    # ✅ ดึงจำนวนนักเรียนที่เรียนในวิชาที่ครูดูแล (ใช้ `distinct()` ป้องกันค่าซ้ำ)
    student_count = StudentProfile.objects.filter(exam_subjects__in=subjects).distinct().count()

    # ✅ ดึงจำนวนการเช็คชื่อเข้าสอบของนักเรียนที่เกี่ยวข้องกับครู
    exam_checkins = Attendance.objects.filter(subject__in=subjects).count()

    return render(request, 'app/teacher/dashboard_teacher.html', {
        'subject_count': subject_count,
        'student_count': student_count,
        'exam_checkins': exam_checkins
    })

@csrf_exempt
@login_required
def teacher_checkin(request):
    """ ฟังก์ชันให้ครูสแกน QR Code เพื่อเช็คชื่อ """
    if request.method == "POST":
        data = json.loads(request.body)
        subject_id = data.get("subject_id")
        subject = get_object_or_404(ExamSubject, id=subject_id)

        if request.user.teacher_profile != subject.invigilator:
            return JsonResponse({"status": "error", "message": "คุณไม่ใช่ผู้คุมสอบของวิชานี้"})

        # ✅ อัปเดตสถานะครู
        subject.invigilator_checkin = True
        subject.save()

        # ✅ ปรับสถานะของครูในฐานข้อมูลให้เป็น "on_time"
        attendance, created = Attendance.objects.get_or_create(student=None, subject=subject)
        attendance.status = "on_time"  # กำหนดให้ครูคุมสอบผ่าน
        attendance.save()

        return JsonResponse({"status": "success"})

@csrf_exempt
@login_required
def confirm_exam_entry_teacher(request):
    """ ฟังก์ชันยืนยันการเข้าสอบของครู """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            subject_id = data.get("subject_id")

            if not subject_id:
                return JsonResponse({"status": "error", "message": "❌ ไม่มี subject_id"}, status=400)

            subject = get_object_or_404(ExamSubject, id=subject_id)

            # ตรวจสอบว่าใช่ครูคุมสอบหรือไม่
            if request.user.teacher_profile != subject.invigilator:
                return JsonResponse({"status": "error", "message": "❌ คุณไม่ใช่ครูคุมสอบของวิชานี้"}, status=403)

            # อัปเดตสถานะการคุมสอบของครู
            subject.invigilator_checkin = True
            subject.save()

            return JsonResponse({"status": "success", "message": "✅ คุณได้เช็คชื่อการคุมสอบแล้ว!"})

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "❌ ข้อมูล JSON ไม่ถูกต้อง"}, status=400)

    return JsonResponse({"status": "error", "message": "❌ Method Not Allowed"}, status=405)

@login_required
def exam_subjects_teacher(request):
    user = request.user

    # ✅ ตรวจสอบว่าผู้ใช้เป็นครูจริง
    try:
        teacher_profile = TeacherProfile.objects.get(user=user)
    except TeacherProfile.DoesNotExist:
        teacher_profile = None

    if not teacher_profile:
        return render(request, 'app/error.html', {'message': 'คุณไม่ได้เป็นครู'})

    # ✅ ดึงโรงเรียนของครู
    school_name = teacher_profile.user.school_name

    # ✅ ดึงระดับชั้นทั้งหมด และลบค่าซ้ำ
    all_classes = ExamSubject.objects.filter(invigilator=teacher_profile).values_list("students__student_class", flat=True).distinct()

    # ✅ ตรวจสอบว่ามีการเลือกระดับชั้นไหม
    selected_class = request.GET.get("student_class", "all")

    # ✅ ดึงเฉพาะวิชาที่ครูคุมสอบ
    subjects = ExamSubject.objects.filter(invigilator=teacher_profile)

    if selected_class != "all":
        subjects = subjects.filter(students__student_class=selected_class)

    # ✅ ใช้ distinct() ป้องกันค่าซ้ำ
    subjects = subjects.distinct()

    # ✅ แปลงค่าระดับชั้นในแต่ละวิชาให้เป็น set (ลบค่าซ้ำ)
    for subject in subjects:
        subject.student_classes = set(subject.students.values_list('student_class', flat=True))

    return render(request, "app/teacher/exam_subjects_teacher.html", {
        "subjects": subjects,
        "all_classes": all_classes,
        "selected_class": selected_class,
        "school_name": school_name  # ✅ ส่งค่าโรงเรียนไปยังเทมเพลต
    })

@login_required
def teacher_check_student(request):
    """
    ✅ ครูดูได้เฉพาะวิชาที่ตัวเองคุมสอบ
    ✅ ตรวจสอบว่า `teacher_profile` มีอยู่หรือไม่
    ✅ ถ้าไม่มี `teacher_profile` ให้แจ้งเตือน
    """
    teacher_profile = getattr(request.user, 'teacher_profile', None)

    if not teacher_profile:
        return HttpResponseForbidden("❌ คุณไม่มีโปรไฟล์ครู กรุณาติดต่อแอดมิน")

    # ✅ ดึงเฉพาะวิชาที่ครูคุมสอบ
    subjects = ExamSubject.objects.filter(invigilator=teacher_profile)

    # ✅ จัดกลุ่มระดับชั้นของนักเรียนแต่ละวิชา
    subject_data = []
    for subject in subjects:
        student_classes = list(set(subject.students.values_list('student_class', flat=True)))  # ใช้ set() เพื่อลบค่าซ้ำ
        subject_data.append({
            "subject": subject,
            "student_classes": student_classes
        })

    return render(request, 'app/teacher/teacher_check_student.html', {
        'subject_data': subject_data
    })

@login_required
def dashboard_student(request):
    try:
        student_profile = request.user.studentprofile
        student_id = student_profile.id
    except StudentProfile.DoesNotExist:
        student_id = None  # Or handle this case as needed
    return render(request, 'app/student/dashboard_student.html', {'user': request.user, 'student_id': student_id})



