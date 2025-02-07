#views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse,JsonResponse
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

    return render(request, 'app/staff/dashboard_staff.html', {
        'subjects': subjects
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
# Define Thai timezone
thai_tz = pytz.timezone('Asia/Bangkok')

@login_required
def add_exam_subject(request):
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, user=request.user)
        if form.is_valid():
            subject = form.save(commit=False)

            # เพิ่มแถวและที่นั่งต่อแถว
            subject.rows = form.cleaned_data['rows']
            subject.columns = form.cleaned_data['columns']

            # ตั้งค่า timezone เป็น 'Asia/Bangkok'
            thai_tz = pytz.timezone('Asia/Bangkok')
            subject.exam_date = form.cleaned_data['exam_date']
            subject.start_time = timezone.make_aware(form.cleaned_data['start_time'], timezone=thai_tz)
            subject.end_time = timezone.make_aware(form.cleaned_data['end_time'], timezone=thai_tz)

            # ดึงนักเรียนที่อยู่ในระดับชั้นที่เลือก
            selected_class = form.cleaned_data['student_class']
            students = StudentProfile.objects.filter(student_class=selected_class, user__school_name=request.user.school_name)

            # บันทึกข้อมูลวิชา
            subject.save()
            subject.students.set(students)
            subject.save()

            messages.success(request, f"✅ เพิ่มรายวิชา {subject.subject_name} พร้อมที่นั่งสำเร็จ!")

            # Redirect ไปหน้ารายการวิชา
            return redirect('exam_subjects_staff')

        else:
            messages.error(request, "❌ ข้อมูลไม่ถูกต้อง กรุณากรอกข้อมูลให้ครบถ้วน")
            print("❌ Form Validation Error:", form.errors)  # Debug Error ใน Console

    else:
        form = ExamSubjectForm(user=request.user)

    return render(request, 'app/staff/add_exam_subject.html', {'form': form})


@login_required
def exam_subjects_staff(request):
    if not request.user.is_staff:
        return HttpResponse("คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้", status=403)

    school_name = request.user.school_name
    subjects = ExamSubject.objects.filter(invigilator__school_name=school_name).select_related('invigilator')

    # ดึงเฉพาะระดับชั้นที่มีในโรงเรียน
    classes = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()

    selected_class = request.GET.get('student_class', 'all')  # Default to 'all' if not provided

    # If the user selects a class other than 'all', filter subjects by class
    if selected_class != 'all' and selected_class:
        subjects = subjects.filter(students__student_class=selected_class)

    return render(request, 'app/staff/exam_subjects_staff.html', {
        'school_name': school_name,
        'subjects': subjects,
        'classes': classes,
        'selected_class': selected_class,
    })


@login_required
def delete_exam_subject(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)
    subject.delete()
    messages.success(request, f"ลบรายวิชา {subject.subject_name} สำเร็จ!")
    return redirect('exam_subjects_staff')

@login_required
def edit_exam_subject(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id, students__user__school_name=request.user.school_name)

    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, instance=subject, user=request.user)
        if form.is_valid():
            subject = form.save(commit=False)

            # ✅ อัปเดตจำนวนแถวและที่นั่งต่อแถว
            subject.rows = form.cleaned_data['rows']
            subject.columns = form.cleaned_data['columns']

            # ✅ อัปเดตระดับชั้นและนักเรียน
            selected_class = form.cleaned_data['student_class']
            students = StudentProfile.objects.filter(student_class=selected_class, user__school_name=request.user.school_name)

            subject.save()
            subject.students.set(students)  # ✅ อัปเดตนักเรียนในวิชา

            messages.success(request, f"✅ แก้ไขรายวิชา {subject.subject_name} สำเร็จ!")
            return redirect('exam_subjects_staff')
        else:
            messages.error(request, "❌ กรุณากรอกข้อมูลให้ถูกต้อง")

    else:
        form = ExamSubjectForm(instance=subject, user=request.user)

    return render(request, 'app/staff/edit_exam_subject.html', {
        'form': form,
        'subject': subject
    })


@login_required
def generate_qr_code(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)

    # ✅ สร้างข้อมูล QR Code
    subject_info = (
        f"📚 วิชา: {subject.subject_name}\n"
        f"📌 รหัส: {subject.subject_code}\n"
        f"📅 วันที่สอบ: {subject.exam_date}\n"
        f"⏰ เวลา: {subject.start_time} - {subject.end_time}\n"
        f"🏫 ห้องสอบ: {subject.room}"
    )

    # ✅ ใช้ `QRCode` และ `PilImage` แทน `qrcode.make()`
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        image_factory=qrcode.image.pil.PilImage  # ✅ ใช้ PIL Image
    )
    qr.add_data(subject_info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # ✅ แปลง QR Code เป็น Base64
    buffer = BytesIO()
    img.save(buffer, "PNG")  # ✅ ไม่ต้องใช้ format="PNG"
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

    return render(request, "app/staff/qr_code.html", {
        "subject": subject,
        "img_base64": img_base64
    })

@login_required
def scan_qr_checkin(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        subject_id = request.POST.get("subject_id")

        student = get_object_or_404(StudentProfile, id=student_id)
        subject = get_object_or_404(ExamSubject, id=subject_id)

        current_time = now()

        # เวลาสอบ
        exam_start_time = subject.start_time
        late_threshold = exam_start_time.replace(hour=exam_start_time.hour, minute=exam_start_time.minute + 30)

        # ตรวจสอบว่านักเรียนเคยเช็คชื่อหรือไม่
        attendance, created = Attendance.objects.get_or_create(student=student, subject=subject)

        if attendance.checkin_time:
            return JsonResponse({"status": "error", "message": "คุณได้เช็คชื่อไปแล้ว"})

        attendance.checkin_time = current_time

        # กำหนดสถานะการเข้าห้องสอบ
        if current_time < exam_start_time:
            attendance.status = "on_time"
        elif current_time <= late_threshold:
            attendance.status = "late"
        else:
            attendance.status = "absent"

        attendance.save()

        return JsonResponse({"status": "success", "attendance_status": attendance.status})

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@login_required
def exam_attendance_status(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)

    # ดึงข้อมูลนักเรียนที่ลงทะเบียนในวิชานี้
    students = subject.students.all()

    # ดึงข้อมูลการเช็คชื่อของนักเรียนในวิชานี้
    attendance_records = Attendance.objects.filter(subject=subject)

    # แปลงเป็น dictionary โดยใช้ student_id เป็น key
    attendance_dict = {att.student.id: att for att in attendance_records}

    return render(request, 'app/staff/exam_attendance_status.html', {
        'subject': subject,
        'students': students,
        'attendance_dict': attendance_dict  # ✅ ส่งเป็น dictionary
    })


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



@csrf_exempt
def teacher_checkin(request):
    """ ฟังก์ชันให้ครูกดเช็คชื่อเข้าคุมสอบ """
    if request.method == "POST":
        data = json.loads(request.body)
        subject_id = data.get("subject_id")
        teacher = TeacherProfile.objects.get(user=request.user)
        subject = ExamSubject.objects.get(id=subject_id)

        if subject.invigilator == teacher:
            return JsonResponse({"status": "success"})
        else:
            return JsonResponse({"status": "error", "message": "คุณไม่ใช่ผู้คุมสอบของวิชานี้"})

    return JsonResponse({"status": "error"}, status=400)


def select_exam_subject(request):
    # ดึงข้อมูลรายวิชาทั้งหมด
    subjects = ExamSubject.objects.prefetch_related('students').all()

    # ดึงระดับชั้นที่มีอยู่ในระบบจากข้อมูลของนักเรียน
    grades = StudentProfile.objects.values_list('student_class', flat=True).distinct()

    # เพิ่มระดับชั้นของแต่ละวิชา
    for subject in subjects:
        subject.grades = list(subject.students.values_list('student_class', flat=True).distinct())

    return render(request, 'app/staff/select_exam_subject.html', {
        'subjects': subjects,
        'grades': grades
    })



@login_required
def dashboard_teacher(request):
    user = request.user
    return render(request, 'app/teacher/dashboard_teacher.html', {'user': user})

@login_required
def exam_subjects_teacher(request):
    if request.user.is_teacher:
        # Fetch subjects where the logged-in teacher is the invigilator
        subjects = ExamSubject.objects.filter(invigilator__user=request.user)
    else:
        # For admin/staff or other users, display all subjects
        subjects = ExamSubject.objects.all()

    school_name = request.user.school_name
    # Fetch distinct student classes for filtering
    classes = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()

    selected_class = request.GET.get('student_class')
    if selected_class and selected_class != "all":
        subjects = subjects.filter(students__student_class=selected_class)

    return render(request, 'app/teacher/exam_subjects_teacher.html', {
        'school_name': school_name,
        'subjects': subjects,
        'classes': classes,
        'selected_class': selected_class,
    })

@login_required
def dashboard_student(request):
    try:
        student_profile = request.user.studentprofile
        student_id = student_profile.id
    except StudentProfile.DoesNotExist:
        student_id = None  # Or handle this case as needed
    return render(request, 'app/student/dashboard_student.html', {'user': request.user, 'student_id': student_id})


def scanner(request):
    user = request.user
    return render(request, 'app/teacher/scaner.html', {'user': user})


def edit_student(request):
    user = request.user
    return render(request, 'app/student/edit_profilestudent.html', {'user': user})

def Examination_history(request):
    user = request.user
    return render(request, 'app/student/Examination_history.html', {'user': user})



