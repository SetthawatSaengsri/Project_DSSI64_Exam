#views.py

from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt

from django.db.models import Q, Count
from django.utils import timezone
from django.utils.timezone import make_aware, localtime, now

from django.db.models import Sum
from .forms import *
from .models import *

import csv
import json
import base64
import pytz
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
import math

import qrcode
import qrcode.image.pil
from PIL import Image

def index_view(request):
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff registration successful.')
            return redirect('index_view')  # After successful registration, stay on the index page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm()

        schools = StaffProfile.objects.values_list('school_name', flat=True).distinct()
    return render(request, 'app/index.html', {'form': form, 'schools': schools})


def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        school_name = request.POST.get('school_name')

        try:
            if User.objects.filter(email=email, is_superuser=True).exists():
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(email=email, school_name=school_name)
        except User.DoesNotExist:
            user = None

        if user and user.check_password(password):
            # Check if user is active (approved by admin)
            if not user.is_active:
                messages.error(request, 'บัญชีของคุณยังไม่ได้รับการอนุมัติจากแอดมิน')
                return redirect('index_view')

            login(request, user)
            if user.is_superuser:
                return redirect('dashboard_admin')  # Redirect to admin dashboard
            elif user.is_student:
                return redirect('dashboard_student')
            elif user.is_teacher:
                return redirect('dashboard_teacher')
            elif user.is_staff:
                return redirect('dashboard_staff')
            else:
                return redirect('index_view')
        else:
            messages.error(request, 'ข้อมูลการเข้าสู่ระบบไม่ถูกต้อง')

    schools = StaffProfile.objects.values_list('school_name', flat=True).distinct()
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
def scanner(request):
    return render(request, 'app/teacher/scanner.html')

##################################################################################################################################################################
@staff_member_required
def dashboard_admin(request):
    teacher_count = TeacherProfile.objects.count()
    student_count = StudentProfile.objects.count()
    subject_count = ExamSubject.objects.count()

    return render(request, 'app/admin/dashboard_admin.html', {
        'teacher_count': teacher_count,
        'student_count': student_count,
        'subject_count': subject_count,
    })

@staff_member_required
def verify_staff_registration(request):
    # ดึงข้อมูลเจ้าหน้าที่ทั้งหมดที่ยังไม่ได้รับการยืนยัน
    unverified_staff = User.objects.filter(is_staff=True, is_active=False)  # กรองเจ้าหน้าที่ที่ยังไม่ได้รับการอนุมัติ

    return render(request, 'app/admin/verify_staff_registration.html', {
        'unverified_staff': unverified_staff
    })

@staff_member_required
def verify_staff_registration_action(request, staff_id):
    staff_user = get_object_or_404(User, id=staff_id)

    # อนุมัติการสมัครโดยการตั้งค่า is_active เป็น True
    if staff_user.is_staff and not staff_user.is_active:
        staff_user.is_active = True  # ทำให้เจ้าหน้าที่สามารถล็อกอินได้หลังจากได้รับการอนุมัติ
        staff_user.save()

        messages.success(request, 'เจ้าหน้าที่ได้รับการยืนยันการสมัครแล้ว!')
    else:
        messages.error(request, 'ไม่สามารถยืนยันการสมัครได้')

    return redirect('verify_staff_registration')

# ฟังก์ชันยกเลิกการสมัคร
def cancel_staff_registration(request, staff_id):
    staff_user = get_object_or_404(User, id=staff_id)

    # ลบผู้ใช้หรือทำการยกเลิกการสมัคร
    if staff_user.is_staff and not staff_user.is_active:
        staff_user.delete()
        messages.success(request, 'การสมัครเจ้าหน้าที่ถูกยกเลิกเรียบร้อยแล้ว!')
    else:
        messages.error(request, 'ไม่สามารถยกเลิกการสมัครได้')

    return redirect('verify_staff_registration')

@staff_member_required
def manage_users(request):
    school_filter = request.GET.get('school')
    if school_filter:
        users = User.objects.filter(school_name=school_filter).order_by('id')
    else:
        users = User.objects.all().order_by('id')
    
    # ดึงรายชื่อโรงเรียนที่มีอยู่ (ไม่ใช่ค่าว่าง)
    schools = User.objects.exclude(school_name__isnull=True).exclude(school_name="").values_list('school_name', flat=True).distinct()
    
    # จัดกลุ่มผู้ใช้ตามบทบาท
    teachers = users.filter(is_teacher=True)
    students = users.filter(is_student=True)
    # สมมุติว่า "เจ้าหน้าที่" คือผู้ใช้ที่มี is_staff=True แต่ไม่ใช่ superuser
    staff = users.filter(is_staff=True, is_superuser=False)
    
    context = {
        'schools': schools,
        'school_filter': school_filter,
        'teachers': teachers,
        'students': students,
        'staff': staff,
    }
    return render(request, 'app/admin/manage_users.html', context)

@staff_member_required
def edit_user(request, user_id):
    """ แก้ไขข้อมูลยูสเซอร์ """
    user_instance = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "อัปเดตข้อมูลยูสเซอร์เรียบร้อยแล้ว")
            return redirect('manage_users')
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอกอีกครั้ง")
    else:
        form = UserEditForm(instance=user_instance)
    return render(request, 'app/admin/edit_user.html', {'form': form, 'user_instance': user_instance})

@staff_member_required
def delete_user(request, user_id):
    """ ลบยูสเซอร์ออกจากระบบ """
    user_instance = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user_instance.delete()
        messages.success(request, "ลบยูสเซอร์เรียบร้อยแล้ว")
        return redirect('manage_users')
    return render(request, 'app/admin/delete_user.html', {'user_instance': user_instance})

##################################################################################################################################################################

@staff_member_required
@login_required
def dashboard_staff(request):
    school_name = request.user.school_name

    teacher_count = TeacherProfile.objects.filter(user__school_name=school_name).count()
    student_count = StudentProfile.objects.filter(user__school_name=school_name).count()
    subject_count = ExamSubject.objects.filter(invigilator__school_name=school_name).count()

    overview_cards = [
        {"label": "จำนวนครู", "count": teacher_count, "color": "indigo", "icon": "👨‍🏫"},
        {"label": "จำนวนนักเรียน", "count": student_count, "color": "emerald", "icon": "🎓"},
        {"label": "จำนวนรายวิชา", "count": subject_count, "color": "pink", "icon": "📚"},
    ]

    class_list = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()
    year_list = ExamSubject.objects.filter(invigilator__school_name=school_name).values_list('academic_year', flat=True).distinct()

    attendance_data = {
        "all": {
            "on_time": 0,
            "late": 0,
            "absent": 0,
            "total_students": student_count,
            "total_teachers": teacher_count,
            "total_subjects": subject_count,
        }
    }

    for class_name in class_list:
        students = StudentProfile.objects.filter(student_class=class_name, user__school_name=school_name)
        student_ids = students.values_list('id', flat=True)

        attendance_data[class_name] = {
            "on_time": 0,
            "late": 0,
            "absent": 0,
            "total_students": students.count(),
            "total_subjects": ExamSubject.objects.filter(students__student_class=class_name, invigilator__school_name=school_name).distinct().count(),
            "total_teachers": teacher_count,
        }

        records = Attendance.objects.filter(student_id__in=student_ids).values("status").annotate(count=Count("id"))
        for record in records:
            status_key = record["status"]
            attendance_data[class_name][status_key] += record["count"]
            attendance_data["all"][status_key] += record["count"]

        for year in year_list:
            subjects = ExamSubject.objects.filter(
                students__student_class=class_name,
                academic_year=year,
                invigilator__school_name=school_name
            ).distinct()

            students_in_year = StudentProfile.objects.filter(
                student_class=class_name,
                user__school_name=school_name
            )
            student_ids = students_in_year.values_list("id", flat=True)
            key = f"{class_name}-{year}"

            attendance_data[key] = {
                "on_time": 0,
                "late": 0,
                "absent": 0,
                "total_students": students_in_year.count(),
                "total_teachers": teacher_count,
                "total_subjects": subjects.count(),
            }

            if subjects.exists():
                records = Attendance.objects.filter(
                    student_id__in=student_ids,
                    subject__academic_year=year
                ).values("status").annotate(count=Count("id"))
                for record in records:
                    status_key = record["status"]
                    attendance_data[key][status_key] += record["count"]
            else:
                attendance_data[key]["on_time"] = 0
                attendance_data[key]["late"] = 0
                attendance_data[key]["absent"] = 0

    for key in attendance_data:
        attendance_data[key].setdefault("on_time", 0)
        attendance_data[key].setdefault("late", 0)
        attendance_data[key].setdefault("absent", 0)
        attendance_data[key].setdefault("total_teachers", teacher_count)
        attendance_data[key].setdefault("total_students", 0)
        attendance_data[key].setdefault("total_subjects", 0)

    context = {
        "school_name": school_name,
        "class_list": class_list,
        "year_list": year_list,
        "attendance_data": attendance_data,
        "overview_cards": overview_cards,
    }

    return render(request, "app/staff/dashboard_staff.html", context)



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
def import_exam_subjects_csv(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'กรุณาเลือกไฟล์เพื่ออัปโหลด')
            return redirect('import_exam_subjects_csv')

        imported_count = 0
        try:
            # ✅ ดึงชื่อโรงเรียนของ staff ที่กำลังล็อกอิน
            school_name = request.user.school_name
 
            # อ่านไฟล์ CSV หรือ Excel
            if file.name.endswith('.csv'):
                raw_data = file.read()
                detected = chardet.detect(raw_data)
                encoding = detected.get("encoding", "utf-8")
                from io import StringIO
                decoded_data = raw_data.decode(encoding)
                df = pd.read_csv(StringIO(decoded_data))
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                messages.error(request, 'รองรับเฉพาะไฟล์ CSV หรือ Excel เท่านั้น')
                return redirect('import_exam_subjects_csv')

            for _, row in df.iterrows():
                required_fields = [
                    'Subject_Name', 'Subject_Code', 'Academic_Year',
                    'Exam_Date', 'Start_Time', 'End_Time',
                    'Room', 'Invigilator', 'Student_Class'
                ]
                if not all(str(row.get(field)).strip() for field in required_fields):
                    messages.warning(request, f"ข้อมูลไม่ครบถ้วนสำหรับ: {row.get('Subject_Name', 'ไม่ระบุชื่อวิชา')}")
                    continue

                # แปลงวันสอบ
                exam_date = pd.to_datetime(row['Exam_Date'], errors='coerce').date()

                # แปลงเวลาเริ่มสอบและสิ้นสุดสอบ
                def get_time(value):
                    if isinstance(value, datetime):
                        return value.time()
                    elif isinstance(value, time):
                        return value
                    else:
                        return pd.to_datetime(value, errors='coerce').time()

                start_time = get_time(row['Start_Time'])
                end_time = get_time(row['End_Time'])

                start_datetime = timezone.make_aware(datetime.combine(exam_date, start_time), timezone=thai_tz)
                end_datetime = timezone.make_aware(datetime.combine(exam_date, end_time), timezone=thai_tz)

                room = row['Room']

                # ✅ ตรวจสอบ "ห้องซ้ำเวลา" ในโรงเรียนเดียวกันเท่านั้น
                if ExamSubject.objects.filter(
                    room=room, exam_date=exam_date, school_name=school_name
                ).filter(start_time__lt=end_datetime, end_time__gt=start_datetime).exists():
                    messages.error(request, f"❌ ห้อง {room} ซ้ำเวลาสอบ")
                    continue

                # ✅ สร้างรายวิชา (ใส่ school_name)
                subject = ExamSubject(
                    subject_name=row['Subject_Name'],
                    subject_code=row['Subject_Code'],
                    academic_year=row['Academic_Year'],
                    exam_date=exam_date,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    room=room,
                    school_name=school_name  # ✅ กำหนดโรงเรียน
                )

                # ✅ ตรวจสอบครูคุมสอบหลัก (เฉพาะในโรงเรียนเดียวกัน)
                try:
                    invigilator = TeacherProfile.objects.get(teacher_id=str(row['Invigilator']).strip(), school_name=school_name)
                    busy = ExamSubject.objects.filter(
                        invigilator=invigilator, exam_date=exam_date, school_name=school_name
                    ).filter(start_time__lt=end_datetime, end_time__gt=start_datetime).exists()
                    if busy:
                        messages.error(request, f"❌ ครู {invigilator.user.get_full_name()} ซ้ำเวลา")
                        continue
                    subject.invigilator = invigilator
                except TeacherProfile.DoesNotExist:
                    messages.warning(request, f"ไม่พบครูคุมสอบ: {row['Invigilator']}")
                    continue

                # ✅ ตรวจสอบครูสำรอง (เฉพาะในโรงเรียนเดียวกัน)
                sec_id = str(row.get('Secondary_Invigilator', '')).strip()
                if sec_id:
                    try:
                        sec_teacher = TeacherProfile.objects.get(teacher_id=sec_id, school_name=school_name)
                        subject.secondary_invigilator = sec_teacher
                    except TeacherProfile.DoesNotExist:
                        messages.warning(request, f"ไม่พบครูผู้คุมสอบสำรอง")

                # ✅ ดึงนักเรียนเฉพาะโรงเรียนปัจจุบัน
                students = StudentProfile.objects.filter(
                    student_class=row['Student_Class'],
                    user__school_name=school_name
                )

                subject.save()
                subject.students.set(students)
                imported_count += 1

            messages.success(request, f"✅ นำเข้าวิชาเรียบร้อยแล้ว: {imported_count} วิชา")

        except Exception as e:
            messages.error(request, f"❌ เกิดข้อผิดพลาด: {e}")

        return redirect('import_exam_subjects_csv')

    return render(request, 'app/staff/import_exam_subjects_csv.html')


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

thai_tz = pytz.timezone('Asia/Bangkok')

# ฟังก์ชันที่กรองและจัดเรียงระดับชั้น
def exam_subjects_staff(request):
    if not request.user.is_staff:
        return HttpResponse("คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้", status=403)

    school_name = request.user.school_name
    subjects = ExamSubject.objects.filter(invigilator__school_name=school_name).select_related('invigilator')

    # ดึงระดับชั้นทั้งหมดและทำการจัดเรียงให้เป็นลำดับที่ถูกต้อง
    classes = StudentProfile.objects.filter(user__school_name=school_name).values_list('student_class', flat=True).distinct()
    classes = sorted(classes, key=lambda x: (int(x.split('/')[0].replace('ม.', '')), int(x.split('/')[1])))

    # ดึงปีการศึกษาทั้งหมด
    academic_years = subjects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    # รับค่าที่เลือกจาก dropdown
    selected_class = request.GET.get('student_class', 'all')
    selected_year = request.GET.get('academic_year', 'all')
    selected_term = request.GET.get('term', 'all')

    # กรองตามระดับชั้น
    if selected_class != 'all' and selected_class:
        subjects = subjects.filter(students__student_class=selected_class)

    # กรองตามปีการศึกษา
    if selected_year != 'all' and selected_year:
        subjects = subjects.filter(academic_year=selected_year)

    # กรองเทอมที่เกี่ยวข้อง
    if selected_year != 'all' and selected_class != 'all':
        terms = subjects.filter(academic_year=selected_year, students__student_class=selected_class).values_list('term', flat=True).distinct()
    else:
        terms = [1, 2, 3]  # หากไม่ได้เลือกทั้งปีการศึกษาและระดับชั้น ให้แสดงทุกเทอม

    subjects = subjects.distinct()

    # ✅ เพิ่มส่วนนี้: สร้าง student_classes สำหรับแต่ละ subject
    for subject in subjects:
        # ดึงระดับชั้นของนักเรียนที่เรียนในวิชานี้
        student_classes = subject.students.values_list('student_class', flat=True).distinct()
        # แปลงเป็น list และเรียงลำดับ
        subject.student_classes = sorted(list(set(student_classes)))

    return render(request, 'app/staff/exam_subjects_staff.html', {
        'school_name': school_name,
        'subjects': subjects,
        'classes': classes,
        'selected_class': selected_class,
        'academic_years': academic_years,
        'selected_year': selected_year,
        'terms': terms,
        'selected_term': selected_term,
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

@staff_member_required
def add_exam_room(request):
    # จัดการการส่งฟอร์ม
    if request.method == 'POST':
        # จัดการการเพิ่มอาคาร
        if 'add_building' in request.POST:
            building_form = BuildingForm(request.POST)
            room_form = ExamRoomForm()  # สร้างฟอร์มห้องเปล่า
            
            if building_form.is_valid():
                building_form.save()
                messages.success(request, "✅ เพิ่มอาคารเรียบร้อยแล้ว")
                return redirect('add_exam_room')
            else:
                # แสดงข้อผิดพลาดของฟอร์ม
                for field in building_form:
                    for error in field.errors:
                        messages.error(request, f"{field.label}: {error}")
        
        # จัดการการเพิ่มห้องสอบ
        elif 'add_room' in request.POST:
            room_form = ExamRoomForm(request.POST)
            building_form = BuildingForm()  # สร้างฟอร์มอาคารเปล่า
            
            if room_form.is_valid():
                room_form.save()
                messages.success(request, "✅ เพิ่มห้องสอบเรียบร้อยแล้ว")
                return redirect('add_exam_room')
            else:
                # แสดงข้อผิดพลาดของฟอร์ม
                for field in room_form:
                    for error in field.errors:
                        messages.error(request, f"{field.label}: {error}")
    else:
        # GET request - สร้างฟอร์มเปล่า
        room_form = ExamRoomForm()
        building_form = BuildingForm()

    # คำนวณสถิติ
    total_buildings = Building.objects.count()
    total_rooms = ExamRoom.objects.count()
    total_capacity = ExamRoom.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
    
    # ดึงรายการอาคารทั้งหมดสำหรับ dropdown
    buildings = Building.objects.all().order_by('code')

    context = {
        'room_form': room_form,
        'building_form': building_form,
        'buildings': buildings,
        'total_buildings': total_buildings,
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
    }

    return render(request, 'app/staff/add_exam_room.html', context)


def find_available_room(exam_date, start_time, end_time, school_name):
    all_rooms = ExamRoom.objects.all()
    used_rooms = ExamSubject.objects.filter(
        exam_date=exam_date,
        start_time__lt=end_time,
        end_time__gt=start_time,
        school_name=school_name
    ).values_list('room_id', flat=True)
    return all_rooms.exclude(id__in=used_rooms).first() 

@staff_member_required
def list_exam_rooms(request):
    # ดึงข้อมูลอาคารพร้อมห้องที่เกี่ยวข้อง
    buildings = Building.objects.all().prefetch_related('rooms').order_by('code')
    
    # คำนวณสถิติสำหรับแต่ละอาคาร
    building_stats = []
    for building in buildings:
        rooms = building.rooms.all()
        total_capacity = sum(room.capacity for room in rooms)
        building_stats.append({
            'building': building,
            'room_count': rooms.count(),
            'total_capacity': total_capacity,
            'rooms': rooms
        })
    
    # สถิติรวม
    total_buildings = buildings.count()
    total_rooms = ExamRoom.objects.count()
    total_capacity = ExamRoom.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
    
    context = {
        'building_stats': building_stats,
        'total_buildings': total_buildings,
        'total_rooms': total_rooms,
        'total_capacity': total_capacity,
    }
    
    return render(request, 'app/staff/list_exam_rooms.html', context)

# เพิ่มฟังก์ชันลบอาคาร
@staff_member_required
def delete_building(request, building_id):
    if request.method == 'POST':
        building = get_object_or_404(Building, id=building_id)
        building_name = building.name
        
        # ตรวจสอบว่ามีห้องในอาคารหรือไม่
        if building.rooms.exists():
            messages.error(request, f"❌ ไม่สามารถลบอาคาร {building_name} ได้ เนื่องจากมีห้องสอบอยู่")
        else:
            building.delete()
            messages.success(request, f"✅ ลบอาคาร {building_name} เรียบร้อยแล้ว")
    
    return redirect('list_exam_rooms')


# เพิ่มฟังก์ชันลบห้องสอบ
@staff_member_required
def delete_exam_room(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(ExamRoom, id=room_id)
        room_name = f"{room.building.name} ห้อง {room.name}"
        
        # ตรวจสอบว่ามีการใช้งานห้องหรือไม่
        if ExamSubject.objects.filter(room=room).exists():
            messages.error(request, f"❌ ไม่สามารถลบ {room_name} ได้ เนื่องจากมีการใช้งานในการสอบ")
        else:
            room.delete()
            messages.success(request, f"✅ ลบ {room_name} เรียบร้อยแล้ว")
    
    return redirect('list_exam_rooms')   

# เพิ่มฟังก์ชันแก้ไขอาคาร
@staff_member_required
def edit_building(request, building_id):
    building = get_object_or_404(Building, id=building_id)
    
    if request.method == 'POST':
        form = BuildingForm(request.POST, instance=building)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ แก้ไขอาคาร {building.name} เรียบร้อยแล้ว")
            return redirect('list_exam_rooms')
    else:
        form = BuildingForm(instance=building)
    
    return render(request, 'app/staff/edit_building.html', {
        'form': form,
        'building': building
    })


# เพิ่มฟังก์ชันแก้ไขห้องสอบ
@staff_member_required
def edit_exam_room(request, room_id):
    room = get_object_or_404(ExamRoom, id=room_id)
    
    if request.method == 'POST':
        form = ExamRoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"✅ แก้ไขห้อง {room.name} เรียบร้อยแล้ว")
            return redirect('list_exam_rooms')
    else:
        form = ExamRoomForm(instance=room)
    
    # ดึงรายการอาคารสำหรับ dropdown
    buildings = Building.objects.all().order_by('code')
    
    return render(request, 'app/staff/edit_exam_room.html', {
        'form': form,
        'room': room,
        'buildings': buildings
    })

@login_required
def building_detail(request, building_id):
    building = get_object_or_404(Building, id=building_id)
    rooms = ExamRoom.objects.filter(building=building)
    return render(request, 'app/staff/building_detail.html', {'building': building, 'rooms': rooms})

THAI_TZ = pytz.timezone('Asia/Bangkok')

# ในไฟล์ views.py - เพิ่ม debug ในฟังก์ชัน add_exam_subject_enhanced

@login_required
def add_exam_subject_enhanced(request):
    """
    ฟังก์ชันเพิ่มรายวิชา รองรับการจัดห้องอัตโนมัติและเลือกเอง
    แก้ไขการจัดการ timezone + เพิ่ม debug
    """
    if request.method == 'POST':
        print("=== POST REQUEST DEBUG ===")
        
        form = ExamSubjectForm(request.POST, user=request.user)
        
        if not form.is_valid():
            print("=== FORM ERRORS ===")
            print(f"Form errors: {form.errors}")
            
            # แสดง error แต่ละ field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"❌ {field}: {error}")
            
            return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
        
        # ✅ ฟอร์มถูกต้อง ดำเนินการต่อ
        try:
            # ดึงข้อมูลจากฟอร์มที่ผ่านการตรวจสอบแล้ว
            cleaned_data = form.cleaned_data
            exam_date = cleaned_data['exam_date']
            start_time = cleaned_data.get('start_time')  # datetime object จาก clean()
            end_time = cleaned_data.get('end_time')      # datetime object จาก clean()
            room_assignment_type = cleaned_data['room_assignment_type']
            selected_class = cleaned_data['student_class']
            school_name = request.user.school_name
            
            print(f"=== CLEANED DATA ===")
            print(f"exam_date: {exam_date}")
            print(f"start_time: {start_time}")
            print(f"end_time: {end_time}")
            print(f"room_assignment_type: {room_assignment_type}")
            print(f"selected_class: {selected_class}")
            print(f"school_name: {school_name}")
            
            # ตรวจสอบว่า user มี school_name หรือไม่
            if not school_name:
                messages.error(request, "❌ ไม่พบข้อมูลโรงเรียนของผู้ใช้")
                return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
            
            # นับจำนวนนักเรียน
            students = StudentProfile.objects.filter(
                student_class=selected_class,
                user__school_name=school_name
            )
            student_count = students.count()
            print(f"📚 จำนวนนักเรียนในชั้น {selected_class}: {student_count} คน")
            
            if student_count == 0:
                messages.error(request, f"❌ ไม่พบนักเรียนในระดับชั้น {selected_class}")
                return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
            
            # ตรวจสอบไม่ให้ซ้ำรหัสวิชา
            existing_subject = ExamSubject.objects.filter(
                subject_code=cleaned_data['subject_code'],
                school_name=school_name,
                academic_year=cleaned_data['academic_year'],
                term=cleaned_data['term']
            ).first()
            
            if existing_subject:
                messages.error(request, f"❌ รหัสวิชา {cleaned_data['subject_code']} มีอยู่แล้วในปีการศึกษา {cleaned_data['academic_year']} เทอม {cleaned_data['term']}")
                return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
            
            # ตรวจสอบความว่างของครู
            invigilator = cleaned_data['invigilator']
            print(f"👨‍🏫 invigilator: {invigilator}")
            
            # ตรวจสอบครูว่าง (ในวันเดียวกัน)
            teacher_busy = ExamSubject.objects.filter(
                Q(invigilator=invigilator) | Q(secondary_invigilator=invigilator),
                school_name=school_name,
                exam_date=exam_date,
            ).exists()
            
            if teacher_busy:
                messages.error(request, f"❌ ครู {invigilator.user.get_full_name()} มีการคุมสอบในวันนี้แล้ว")
                return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
            
            # จัดการห้องสอบ
            selected_room = None
            room_message = ""
            
            if room_assignment_type == 'auto':
                print("🤖 Auto room assignment")
                # หาห้องว่างอัตโนมัติ
                available_rooms = ExamRoom.objects.filter(capacity__gte=student_count)
                used_rooms = ExamSubject.objects.filter(
                    exam_date=exam_date,
                    school_name=school_name
                ).values_list('room_id', flat=True)
                
                available_room = available_rooms.exclude(id__in=used_rooms).order_by('capacity').first()
                
                if not available_room:
                    messages.error(request, f"❌ ไม่มีห้องสอบที่รองรับนักเรียน {student_count} คน")
                    return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
                
                selected_room = available_room
                room_message = f"จัดห้องอัตโนมัติ: {available_room}"
                
            else:  # manual
                print("🎯 Manual room assignment")
                selected_room = cleaned_data.get('room')
                
                if not selected_room:
                    messages.error(request, "❌ กรุณาเลือกห้องสอบ")
                    return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
                
                if selected_room.capacity < student_count:
                    messages.error(request, f"❌ ห้อง {selected_room} มีความจุ {selected_room.capacity} คน แต่มีนักเรียน {student_count} คน")
                    return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
                
                room_message = f"เลือกห้องเอง: {selected_room}"
            
            print(f"🏫 Selected room: {selected_room}")
            
            # บันทึก subject โดยไม่ commit ก่อน
            subject = form.save(commit=False)
            
            # กำหนดค่าเพิ่มเติม
            subject.school_name = school_name
            subject.room = selected_room
            
            # ตั้งค่า QR expiration time
            if end_time:
                if hasattr(end_time, 'time'):
                    subject.qr_expiration = end_time.time()
                else:
                    subject.qr_expiration = end_time
            
            print(f"=== SAVING SUBJECT ===")
            print(f"Final subject data:")
            print(f"  exam_date: {subject.exam_date}")
            print(f"  start_time: {subject.start_time}")
            print(f"  end_time: {subject.end_time}")
            print(f"  school_name: {subject.school_name}")
            print(f"  room: {subject.room}")
            
            # บันทึกข้อมูล
            subject.save()
            subject.students.set(students)
            
            print(f"✅ Subject saved with ID: {subject.id}")
            
            messages.success(request, f"✅ เพิ่มรายวิชา '{subject.subject_name}' สำเร็จ! ({room_message})")
            return redirect('exam_subjects_staff')
            
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})
    
    else:
        print("=== GET REQUEST ===")
        form = ExamSubjectForm(user=request.user)
    
    return render(request, 'app/staff/add_exam_subject_enhanced.html', {'form': form})

def _get_capacity_suggestions(student_count, exam_date, start_time, end_time, school_name):
    """ให้คำแนะนำเมื่อไม่มีห้องเพียงพอ"""
    suggestions = []
    
    # หาห้องที่ใหญ่ที่สุด
    largest_room = ExamRoom.objects.order_by('-capacity').first()
    if largest_room:
        suggestions.append(f"💡 ห้องที่ใหญ่ที่สุด: {largest_room} (ความจุ {largest_room.capacity} คน)")
    
    # คำนวณจำนวนห้องที่ต้องการ
    avg_capacity = ExamRoom.objects.aggregate(avg_cap=models.Avg('capacity'))['avg_cap'] or 30
    required_rooms = math.ceil(student_count / avg_capacity)
    suggestions.append(f"💡 จำเป็นต้องใช้ประมาณ {required_rooms} ห้อง สำหรับนักเรียน {student_count} คน")
    
    # แนะนำเปลี่ยนเวลา
    suggestions.append("💡 ลองเปลี่ยนเวลาสอบ หรือแบ่งเป็นหลายช่วงเวลา")
    
    return suggestions

# ✅ ฟังก์ชันช่วยที่แก้ไขแล้ว
def _is_teacher_busy_naive(teacher, exam_date, start_datetime, end_datetime, school_name, is_secondary=False):
    """ตรวจสอบว่าครูไม่ว่างหรือไม่ - ใช้ naive datetime"""
    if is_secondary:
        busy_check = ExamSubject.objects.filter(
            Q(secondary_invigilator=teacher) | Q(invigilator=teacher),
            school_name=school_name,
            exam_date=exam_date
        )
    else:
        busy_check = ExamSubject.objects.filter(
            Q(invigilator=teacher) | Q(secondary_invigilator=teacher),
            school_name=school_name,
            exam_date=exam_date
        )
    
    # ✅ เปรียบเทียบด้วย time แทน datetime
    return busy_check.filter(
        start_time__time__lt=end_datetime.time(),
        end_time__time__gt=start_datetime.time()
    ).exists()


def _find_available_room_naive(exam_date, start_datetime, end_datetime, school_name, student_count=None):
    """หาห้องที่ว่างในช่วงเวลาที่กำหนด - ใช้ naive datetime"""
    used_rooms_ids = ExamSubject.objects.filter(
        school_name=school_name,
        exam_date=exam_date,
        start_time__time__lt=end_datetime.time(),
        end_time__time__gt=start_datetime.time()
    ).values_list('room__id', flat=True)
    
    available_rooms = ExamRoom.objects.exclude(id__in=used_rooms_ids)
    
    if student_count:
        available_rooms = available_rooms.filter(capacity__gte=student_count)
    
    available_room = available_rooms.order_by('capacity').first()
    
    if available_room:
        building_name = available_room.building.name if available_room.building else "⚠️ ไม่มีอาคาร"
        print(f"✅ จัดห้องอัตโนมัติ: {building_name} ห้อง {available_room.name} (ความจุ {available_room.capacity} คน, นักเรียน {student_count or 'ไม่ระบุ'} คน)")
    else:
        print(f"❌ ไม่มีห้องว่างสำหรับ {student_count} คน ในเวลา {start_datetime.time()} - {end_datetime.time()}")
    
    return available_room


def _is_room_busy_naive(room, exam_date, start_datetime, end_datetime, school_name):
    """ตรวจสอบว่าห้องไม่ว่างหรือไม่ - ใช้ naive datetime"""
    is_busy = ExamSubject.objects.filter(
        room=room,
        school_name=school_name,
        exam_date=exam_date,
        start_time__time__lt=end_datetime.time(),
        end_time__time__gt=start_datetime.time()
    ).exists()
    
    if is_busy:
        conflicting_subjects = ExamSubject.objects.filter(
            room=room,
            school_name=school_name,
            exam_date=exam_date,
            start_time__time__lt=end_datetime.time(),
            end_time__time__gt=start_datetime.time()
        )
        print(f"❌ ห้อง {room} ถูกใช้โดย:")
        for subject in conflicting_subjects:
            print(f"   - {subject.subject_name} ({subject.start_time.strftime('%H:%M')} - {subject.end_time.strftime('%H:%M')})")
    
    return is_busy


# AJAX endpoint สำหรับดึงห้องตามอาคาร
@login_required
def get_rooms_by_building(request):
    """API สำหรับดึงรายการห้องตามอาคารที่เลือก"""
    building_id = request.GET.get('building_id')
    if building_id:
        try:
            rooms = ExamRoom.objects.filter(building_id=building_id).order_by('name')
            room_data = []
            for room in rooms:
                room_data.append({
                    'id': room.id,
                    'name': room.name,
                    'capacity': room.capacity,
                    'full_name': f"{room.building.name} ห้อง {room.name}"
                })
            return JsonResponse({'rooms': room_data, 'success': True})
        except Exception as e:
            return JsonResponse({'rooms': [], 'success': False, 'error': str(e)})
    return JsonResponse({'rooms': [], 'success': False, 'error': 'No building ID provided'})

# ฟังก์ชันเสริมสำหรับตรวจสอบความพร้อมของห้อง
@login_required
def check_room_availability(request):
    """ตรวจสอบความพร้อมของห้องในเวลาที่กำหนด"""
    if request.method == 'POST':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        exam_date = data.get('exam_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        try:
            room = ExamRoom.objects.get(id=room_id)
            exam_date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            start_datetime = timezone.make_aware(
                datetime.combine(exam_date_obj, datetime.strptime(start_time, '%H:%M').time()),
                timezone=thai_tz
            )
            end_datetime = timezone.make_aware(
                datetime.combine(exam_date_obj, datetime.strptime(end_time, '%H:%M').time()),
                timezone=thai_tz
            )
            
            is_busy = _is_room_busy(room, exam_date_obj, start_datetime, end_datetime, request.user.school_name)
            
            # หาวิชาที่ใช้ห้องในเวลานั้น (ถ้ามี)
            conflicting_subjects = ExamSubject.objects.filter(
                room=room,
                school_name=request.user.school_name,
                exam_date=exam_date_obj,
                start_time__lt=end_datetime,
                end_time__gt=start_datetime
            )
            
            conflict_details = []
            for subject in conflicting_subjects:
                conflict_details.append({
                    'subject_name': subject.subject_name,
                    'subject_code': subject.subject_code,
                    'start_time': subject.start_time.strftime('%H:%M'),
                    'end_time': subject.end_time.strftime('%H:%M')
                })
            
            return JsonResponse({
                'available': not is_busy,
                'room_name': str(room),
                'conflicts': conflict_details
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# ฟังก์ชันสำหรับดึงสถิติห้องสอบ
@login_required
def get_room_statistics(request):
    """ดึงสถิติการใช้งานห้องสอบ"""
    total_rooms = ExamRoom.objects.count()
    total_buildings = Building.objects.count()
    
    # นับจำนวนห้องที่ถูกใช้งานในวันนี้
    today = timezone.now().date()
    rooms_in_use_today = ExamSubject.objects.filter(
        exam_date=today,
        school_name=request.user.school_name
    ).values_list('room_id', flat=True).distinct().count()
    
    # นับจำนวนวิชาสอบวันนี้
    exams_today = ExamSubject.objects.filter(
        exam_date=today,
        school_name=request.user.school_name
    ).count()
    
    return JsonResponse({
        'total_rooms': total_rooms,
        'total_buildings': total_buildings,
        'rooms_in_use_today': rooms_in_use_today,
        'exams_today': exams_today,
        'room_utilization_percentage': round((rooms_in_use_today / total_rooms * 100) if total_rooms > 0 else 0, 2)
    })

# ฟังก์ชันสำหรับแนะนำห้องสอบที่เหมาะสม
@login_required
def suggest_rooms(request):
    """แนะนำห้องสอบที่เหมาะสมตามจำนวนนักเรียน"""
    if request.method == 'POST':
        data = json.loads(request.body)
        student_class = data.get('student_class')
        exam_date = data.get('exam_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        try:
            # นับจำนวนนักเรียนในชั้น
            student_count = StudentProfile.objects.filter(
                student_class=student_class,
                user__school_name=request.user.school_name
            ).count()
            
            # แปลงเวลา
            exam_date_obj = datetime.strptime(exam_date, git add .
                datetime.combine(exam_date_obj, datetime.strptime(start_time, '%H:%M').time()),
                timezone=thai_tz
            )
            end_datetime = timezone.make_aware(
                datetime.combine(exam_date_obj, datetime.strptime(end_time, '%H:%M').time()),
                timezone=thai_tz
            )
            
            # หาห้องที่ว่างและมีความจุเพียงพอ
            used_rooms_ids = ExamSubject.objects.filter(
                school_name=request.user.school_name,
                exam_date=exam_date_obj,
                start_time__lt=end_datetime,
                end_time__gt=start_datetime
            ).values_list('room_id', flat=True)
            
            available_rooms = ExamRoom.objects.exclude(id__in=used_rooms_ids).filter(
                capacity__gte=student_count
            ).order_by('capacity')
            
            suggestions = []
            for room in available_rooms[:5]:  # แนะนำ 5 ห้องแรก
                efficiency = round((student_count / room.capacity * 100), 2)
                suggestions.append({
                    'id': room.id,
                    'name': room.name,
                    'building': room.building.name,
                    'capacity': room.capacity,
                    'efficiency': efficiency,
                    'full_name': str(room)
                })
            
            return JsonResponse({
                'suggestions': suggestions,
                'student_count': student_count,
                'recommended_capacity': student_count + 5  # เผื่อพิเศษ 5 คน
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def delete_exam_subject(request, subject_id):
    if request.method == 'POST':
        subject = get_object_or_404(ExamSubject, id=subject_id)
        subject.delete()
        messages.success(request, f"ลบรายวิชา {subject.subject_name} สำเร็จ!")
    else:
        messages.error(request, "การลบต้องใช้วิธี POST เท่านั้น")
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

@login_required
def generate_qr_code(request, subject_id):
    """ฟังก์ชันสร้าง QR Code สำหรับยืนยันเข้าสอบ - เพิ่มการทดสอบสำหรับการสอบที่ผ่านมาแล้ว"""
    subject = get_object_or_404(ExamSubject, id=subject_id)
    
    # ✅ ตรวจสอบสิทธิ์การเข้าถึง
    if not (request.user.is_staff or 
            (request.user.is_teacher and hasattr(request.user, 'teacher_profile') and 
             (subject.invigilator == request.user.teacher_profile or 
              subject.secondary_invigilator == request.user.teacher_profile))):
        messages.error(request, "❌ คุณไม่มีสิทธิ์เข้าถึง QR Code นี้")
        return redirect('exam_subjects_staff')
    
    # ✅ ดึงระดับชั้นของนักเรียนที่เรียนในวิชานี้
    student_classes = list(subject.students.values_list('student_class', flat=True).distinct())
    subject.student_classes = sorted(student_classes)  # เรียงลำดับระดับชั้น
    
    # สร้าง URL สำหรับ QR Code
    qr_url = request.build_absolute_uri(f"/exam/confirm_exam_entry/?subject_id={subject_id}")
    
    # ✅ เพิ่ม timestamp เพื่อป้องกันการใช้ซ้ำ
    import time
    timestamp = int(time.time())
    qr_url += f"&t={timestamp}"
    
    try:
        # ✅ สร้าง QR Code ขนาดใหญ่และคมชัด
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=12,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # สร้างภาพ QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # ✅ เพิ่มขนาดภาพสำหรับการพิมพ์
        try:
            img = img.resize((400, 400), Image.Resampling.LANCZOS)
        except AttributeError:
            try:
                img = img.resize((400, 400), Image.LANCZOS)
            except AttributeError:
                img = img.resize((400, 400), Image.ANTIALIAS)
        
        # แปลงเป็น base64
        buffer = BytesIO()
        img.save(buffer, format="PNG", optimize=True, quality=95)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
    except Exception as e:
        print(f"QR Code generation error: {e}")
        # ใช้ QR Code แบบง่าย
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(qr_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # ✅ แก้ไขการจัดการเวลา - ใช้ timezone ที่ถูกต้อง
    thai_tz = pytz.timezone('Asia/Bangkok')
    utc_tz = pytz.UTC
    
    # ✅ ใช้เวลาปัจจุบันใน UTC แล้วแปลงเป็นเวลาไทย
    now_utc = timezone.now()  # เวลาปัจจุบันใน UTC
    now_time = now_utc.astimezone(thai_tz)  # แปลงเป็นเวลาไทย
    
    print(f"🕐 Current time (UTC): {now_utc}")
    print(f"🕐 Current time (Thai): {now_time}")
    print(f"📅 Exam date: {subject.exam_date}")
    print(f"⏰ Start time field: {subject.start_time} (type: {type(subject.start_time)})")
    print(f"⏰ End time field: {subject.end_time} (type: {type(subject.end_time)})")
    
    # ✅ จัดการเวลาเริ่มและสิ้นสุดให้ถูกต้อง
    try:
        # ถ้าเป็น datetime object (มี timezone info แล้ว)
        if hasattr(subject.start_time, 'astimezone'):
            exam_start_time = subject.start_time.astimezone(thai_tz)
            print(f"✅ Start time already datetime: {exam_start_time}")
        else:
            # ✅ สร้าง naive datetime แล้วใช้ pytz localize แทน make_aware
            naive_start = datetime.combine(subject.exam_date, subject.start_time)
            exam_start_time = thai_tz.localize(naive_start)
            print(f"✅ Start time localized: {exam_start_time}")
            
        if hasattr(subject.end_time, 'astimezone'):
            exam_end_time = subject.end_time.astimezone(thai_tz)
            print(f"✅ End time already datetime: {exam_end_time}")
        else:
            # ✅ สร้าง naive datetime แล้วใช้ pytz localize แทน make_aware
            naive_end = datetime.combine(subject.exam_date, subject.end_time)
            exam_end_time = thai_tz.localize(naive_end)
            print(f"✅ End time localized: {exam_end_time}")
            
    except Exception as e:
        print(f"❌ Time conversion error: {e}")
        # ใช้เวลาปัจจุบันเป็นเวลาเริ่มสอบ และบวก 2 ชั่วโมงเป็นเวลาสิ้นสุด
        exam_start_time = now_time
        exam_end_time = now_time + timedelta(hours=2)
        print(f"⚠️ Using fallback times: {exam_start_time} - {exam_end_time}")
    
    # ✅ ตรวจสอบว่าเป็นการสอบในอดีตหรือไม่ (สำหรับการทดสอบ)
    exam_date_today = now_time.date()
    is_past_exam = subject.exam_date < exam_date_today
    
    if is_past_exam:
        print(f"⚠️ TESTING MODE: This is a past exam ({subject.exam_date} vs {exam_date_today})")
        # สำหรับการทดสอบ: ยืดเวลาหมดอายุให้เป็น 24 ชั่วโมงจากตอนนี้
        qr_expiry_time = now_time + timedelta(hours=24)
        print(f"🧪 Extended QR expiry for testing: {qr_expiry_time}")
        
        # ปรับเวลาเริ่มสอบให้เป็นเวลาปัจจุบัน (สำหรับการทดสอบ)
        testing_start_time = now_time - timedelta(minutes=10)  # เริ่มสอบ 10 นาทีที่แล้ว
        testing_end_time = now_time + timedelta(hours=2)       # สิ้นสุดอีก 2 ชั่วโมง
        
        print(f"🧪 Testing times:")
        print(f"   Start: {testing_start_time}")
        print(f"   End: {testing_end_time}")
        print(f"   Expiry: {qr_expiry_time}")
        
        # ใช้เวลาทดสอบ
        exam_start_time = testing_start_time
        exam_end_time = testing_end_time
    else:
        # ✅ เพิ่มเวลาพิเศษ 30 นาทีหลังสิ้นสุดการสอบ (กรณีปกติ)
        qr_expiry_time = exam_end_time + timedelta(minutes=30)
    
    # ✅ ตรวจสอบสถานะ QR Code
    is_expired = now_time > qr_expiry_time
    can_use_early = now_time >= (exam_start_time - timedelta(minutes=30))
    
    print(f"🕐 Current: {now_time}")
    print(f"🕑 Exam start: {exam_start_time}")
    print(f"🕒 Exam end: {exam_end_time}")
    print(f"🕓 QR expiry: {qr_expiry_time}")
    print(f"❓ Is expired: {is_expired}")
    print(f"❓ Can use early: {can_use_early}")
    print(f"🧪 Is past exam (testing mode): {is_past_exam}")
    
    # ✅ แสดงความแตกต่างของเวลา
    if now_time > exam_end_time:
        time_since_exam = now_time - exam_end_time
        print(f"⏱️ Time since exam ended: {time_since_exam}")
    else:
        time_until_exam = exam_start_time - now_time
        print(f"⏱️ Time until exam starts: {time_until_exam}")
    
    # ✅ คำนวณเวลาที่เหลือ
    if now_time < qr_expiry_time:
        time_remaining_seconds = (qr_expiry_time - now_time).total_seconds()
    else:
        time_remaining_seconds = 0
    
    print(f"⏳ Time remaining (seconds): {time_remaining_seconds}")
    
    context = {
        "subject": subject,
        "img_base64": img_base64,
        "qr_url": qr_url,
        "current_time": now_time,
        "exam_start_time": exam_start_time,
        "exam_end_time": exam_end_time,
        "qr_expiry_time": qr_expiry_time,
        "is_expired": is_expired,
        "can_use_early": can_use_early,
        "time_remaining": time_remaining_seconds,
        "is_past_exam": is_past_exam,  # ส่งตัวแปรนี้ไปด้วย
    }

    return render(request, "app/staff/qr_code.html", context)

@csrf_exempt
@login_required
def confirm_exam_entry(request):
    """ฟังก์ชันยืนยันเข้าสอบผ่าน QR Code - แก้ไข error"""
    
    if request.method == "GET":
        subject_id = request.GET.get("subject_id")
        timestamp = request.GET.get("t")
        
        if not subject_id:
            return render(request, "app/error.html", {
                "message": "❌ ไม่พบรหัสวิชา"
            })
        
        try:
            subject = get_object_or_404(ExamSubject, id=subject_id)
            
            # ✅ แก้ไขการจัดการเวลา
            thai_tz = pytz.timezone('Asia/Bangkok')
            now = timezone.now().astimezone(thai_tz)
            
            # ✅ สร้าง datetime จาก date + time แล้วค่อยแปลง timezone
            try:
                if hasattr(subject.end_time, 'astimezone'):
                    # ถ้าเป็น datetime object แล้ว
                    exam_end_time = subject.end_time.astimezone(thai_tz)
                else:
                    # ถ้าเป็น time object ให้รวมกับ exam_date
                    naive_end = datetime.combine(subject.exam_date, subject.end_time)
                    exam_end_time = thai_tz.localize(naive_end)
                
                if hasattr(subject.start_time, 'astimezone'):
                    exam_start_time = subject.start_time.astimezone(thai_tz)
                else:
                    naive_start = datetime.combine(subject.exam_date, subject.start_time)
                    exam_start_time = thai_tz.localize(naive_start)
                    
            except Exception as e:
                print(f"❌ Time conversion error: {e}")
                return render(request, "app/staff/error.html", {
                    "message": f"เกิดข้อผิดพลาดในการคำนวณเวลา: {str(e)}"
                })
            
            qr_expiry_time = exam_end_time + timedelta(minutes=30)
            
            if now > qr_expiry_time:
                return render(request, "app/staff/qr_expired.html", {
                    "subject": subject,
                    "message": "QR Code หมดอายุแล้ว ไม่สามารถใช้งานได้"
                })
            
            # ตรวจสอบว่าอยู่ในช่วงเวลาที่เหมาะสม
            check_in_start = exam_start_time - timedelta(minutes=30)
            
            if now < check_in_start:
                return render(request, "app/staff/qr_too_early.html", {
                    "subject": subject,
                    "check_in_time": check_in_start,
                    "message": f"ยังไม่ถึงเวลาเช็คชื่อ กรุณารอจนถึง {check_in_start.strftime('%H:%M')} น."
                })
            
            # ดำเนินการตามบทบาทผู้ใช้
            student, teacher, seat_number = None, None, None
            
            if request.user.is_student:
                try:
                    student = StudentProfile.objects.get(user=request.user)
                    
                    if not subject.students.filter(id=student.id).exists():
                        return render(request, "app/staff/qr_not_registered.html", {
                            "subject": subject,
                            "message": "คุณไม่ได้ลงทะเบียนในวิชานี้"
                        })
                    
                    # คำนวณเลขที่นั่ง
                    students = list(subject.students.order_by('student_class', 'user__last_name'))
                    for idx, s in enumerate(students, start=1):
                        if s.user.id == request.user.id:
                            seat_number = idx
                            break
                    
                except StudentProfile.DoesNotExist:
                    return render(request, "app/staff/error.html", {
                        "message": "ไม่พบข้อมูลนักเรียน"
                    })
                    
            elif request.user.is_teacher:
                try:
                    teacher = TeacherProfile.objects.get(user=request.user)
                    
                    if (teacher.id != subject.invigilator_id and 
                        teacher.id != getattr(subject.secondary_invigilator, 'id', None)):
                        return render(request, "app/staff/qr_unauthorized.html", {
                            "subject": subject,
                            "message": "คุณไม่ใช่ครูคุมสอบของวิชานี้"
                        })
                        
                except TeacherProfile.DoesNotExist:
                    return render(request, "app/staff/error.html", {
                        "message": "ไม่พบข้อมูลครู"
                    })
            
            context = {
                "subject": subject,
                "student": student,
                "teacher": teacher,
                "seat_number": seat_number,
                "current_time": now,
                "exam_start_time": exam_start_time,
                "exam_end_time": exam_end_time,
                "can_check_in": check_in_start <= now <= qr_expiry_time,
            }
            
            return render(request, "app/staff/confirm_exam.html", context)
            
        except Exception as e:
            print(f"❌ General error: {str(e)}")
            return render(request, "app/staff/error.html", {
                "message": f"เกิดข้อผิดพลาด: {str(e)}"
            })
    
    elif request.method == "POST":
        try:
            data = json.loads(request.body)
            subject_id = data.get("subject_id")
            
            if not subject_id:
                return JsonResponse({"status": "error", "message": "❌ ไม่มี subject_id"}, status=400)
            
            subject = get_object_or_404(ExamSubject, id=subject_id)
            
            # ตรวจสอบเวลาหมดอายุอีกครั้ง
            thai_tz = pytz.timezone('Asia/Bangkok')
            now = timezone.now().astimezone(thai_tz)
            
            # แก้ไขการคำนวณเวลาหมดอายุ
            try:
                if hasattr(subject.end_time, 'astimezone'):
                    exam_end_time = subject.end_time.astimezone(thai_tz)
                else:
                    naive_end = datetime.combine(subject.exam_date, subject.end_time)
                    exam_end_time = thai_tz.localize(naive_end)
                    
                qr_expiry_time = exam_end_time + timedelta(minutes=30)
                
            except Exception as e:
                return JsonResponse({
                    "status": "error", 
                    "message": f"❌ เกิดข้อผิดพลาดในการคำนวณเวลา: {str(e)}"
                }, status=500)
            
            if now > qr_expiry_time:
                return JsonResponse({
                    "status": "error", 
                    "message": "❌ QR Code หมดอายุแล้ว ไม่สามารถเช็คชื่อได้"
                }, status=400)
            
            # ดำเนินการตามบทบาท
            if request.user.is_student:
                student = get_object_or_404(StudentProfile, user=request.user)
                
                existing_attendance = Attendance.objects.filter(
                    student=student, 
                    subject=subject
                ).first()
                
                if existing_attendance:
                    return JsonResponse({
                        "status": "info",
                        "message": f"✅ คุณได้เช็คชื่อไปแล้วเมื่อ {existing_attendance.checkin_time.strftime('%H:%M')} น.",
                        "already_checked": True
                    })
                
                attendance = Attendance.objects.create(
                    student=student,
                    subject=subject,
                    status="on_time",
                    checkin_time=now
                )
                
                return JsonResponse({
                    "status": "success",
                    "message": "✅ เช็คชื่อนักเรียนสำเร็จ!",
                    "checkin_time": now.strftime('%H:%M'),
                    "seat_number": getattr(student, 'seat_number', 'ไม่ระบุ')
                })
                
            elif request.user.is_teacher:
                teacher = get_object_or_404(TeacherProfile, user=request.user)
                
                if teacher.id == subject.invigilator_id:
                    if subject.invigilator_checkin:
                        return JsonResponse({
                            "status": "info",
                            "message": "✅ ครูหลักได้เช็คชื่อไปแล้ว",
                            "already_checked": True
                        })
                    
                    subject.invigilator_checkin = True
                    subject.invigilator_checkin_time = now
                    subject.save()
                    
                    return JsonResponse({
                        "status": "success",
                        "message": "✅ เช็คชื่อครูคุมสอบหลักสำเร็จ!",
                        "position": "main"
                    })
                    
                elif teacher.id == getattr(subject.secondary_invigilator, 'id', None):
                    if subject.secondary_invigilator_checkin:
                        return JsonResponse({
                            "status": "info",
                            "message": "✅ ครูสำรองได้เช็คชื่อไปแล้ว",
                            "already_checked": True
                        })
                    
                    subject.secondary_invigilator_checkin = True
                    subject.secondary_invigilator_checkin_time = now
                    subject.save()
                    
                    return JsonResponse({
                        "status": "success",
                        "message": "✅ เช็คชื่อครูคุมสอบสำรองสำเร็จ!",
                        "position": "secondary"
                    })
                
                else:
                    return JsonResponse({
                        "status": "error",
                        "message": "❌ คุณไม่ใช่ครูคุมสอบของวิชานี้"
                    }, status=403)
            
            else:
                return JsonResponse({
                    "status": "error",
                    "message": "❌ บทบาทผู้ใช้ไม่ถูกต้อง"
                }, status=403)
                
        except json.JSONDecodeError:
            return JsonResponse({
                "status": "error",
                "message": "❌ ข้อมูล JSON ไม่ถูกต้อง"
            }, status=400)
        except Exception as e:
            print(f"❌ POST error: {str(e)}")
            return JsonResponse({
                "status": "error",
                "message": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }, status=500)
    
    return JsonResponse({
        "status": "error",
        "message": "❌ Method ไม่ถูกต้อง"
    }, status=405)


# ✅ เพิ่มฟังก์ชันตรวจสอบสถานะ QR Code
@login_required
def check_qr_status(request, subject_id):
    """ตรวจสอบสถานะ QR Code แบบ Real-time"""
    try:
        subject = get_object_or_404(ExamSubject, id=subject_id)
        
        thai_tz = pytz.timezone('Asia/Bangkok')
        now = timezone.now().astimezone(thai_tz)
        exam_start = subject.start_time.astimezone(thai_tz)
        exam_end = subject.end_time.astimezone(thai_tz)
        qr_expiry = exam_end + timedelta(minutes=30)
        check_in_start = exam_start - timedelta(minutes=30)
        
        # กำหนดสถานะ
        if now < check_in_start:
            status = "too_early"
            message = f"ยังไม่ถึงเวลาเช็คชื่อ (เริ่ม {check_in_start.strftime('%H:%M')} น.)"
        elif now > qr_expiry:
            status = "expired"
            message = "QR Code หมดอายุแล้ว"
        elif exam_start <= now <= exam_end:
            status = "exam_ongoing"
            message = "กำลังสอบ - สามารถเช็คชื่อได้"
        elif check_in_start <= now < exam_start:
            status = "check_in_open"
            message = "เปิดให้เช็คชื่อแล้ว"
        elif exam_end < now <= qr_expiry:
            status = "post_exam"
            message = "หลังสอบ - ยังเช็คชื่อได้"
        else:
            status = "unknown"
            message = "สถานะไม่ทราบ"
        
        return JsonResponse({
            "status": status,
            "message": message,
            "current_time": now.strftime('%H:%M:%S'),
            "exam_start": exam_start.strftime('%H:%M'),
            "exam_end": exam_end.strftime('%H:%M'),
            "qr_expiry": qr_expiry.strftime('%H:%M'),
            "can_use": status in ["check_in_open", "exam_ongoing", "post_exam"],
            "time_remaining": max(0, (qr_expiry - now).total_seconds())
        })
        
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

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

    # ตรวจสอบสิทธิ์เข้าถึงข้อมูล
    if request.user.is_staff:
        pass  # staff ดูได้ทุกวิชา
    elif request.user.is_teacher:
        teacher_profile = getattr(request.user, 'teacher_profile', None)
        # หากเป็นครูหลักเท่านั้นที่จะดูได้ (หรือคุณอาจปรับเงื่อนไขให้ครูทั้งหลักและสำรองดูได้)
        if not teacher_profile or subject.invigilator != teacher_profile:
            return HttpResponseForbidden("❌ คุณไม่มีสิทธิ์ดูวิชานี้")
    else:
        return HttpResponseForbidden("❌ คุณไม่มีสิทธิ์เข้าถึงข้อมูลนี้")

    # รีเฟรชข้อมูลของ subject เพื่อให้ได้ข้อมูลล่าสุด
    subject.refresh_from_db()

    # ดึงนักเรียนที่ลงทะเบียนสอบในวิชานี้
    students = subject.students.all()

    # ดึงข้อมูลการเช็คชื่อ
    attendance_records = Attendance.objects.filter(subject=subject)
    attendance_dict = {att.student.id: att for att in attendance_records}

    return render(request, 'app/staff/exam_attendance_status.html', {
        'subject': subject,
        'students': students,
        'attendance_dict': attendance_dict,
        # ส่งตัวแปรสำหรับสถานะของครูทั้งหลักและครูสำรอง
        'primary_teacher_checked_in': subject.invigilator_checkin,
        'secondary_teacher_checked_in': subject.secondary_invigilator_checkin,
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

##################################################################################################################################################################
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
    if request.method == "POST":
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body)
                subject_id = data.get("subject_id")
                new_status = data.get("status")
            else:
                subject_id = request.POST.get("subject_id")
                new_status = request.POST.get("status")
            
            if not subject_id:
                return JsonResponse({"status": "error", "message": "❌ ไม่มี subject_id"}, status=400)
            
            subject = get_object_or_404(ExamSubject, id=subject_id)
            teacher = TeacherProfile.objects.filter(user=request.user).first()
            
            if not teacher:
                return JsonResponse({"status": "error", "message": "❌ ไม่พบโปรไฟล์ครู"}, status=404)
            
            if teacher.id != subject.invigilator_id and teacher.id != subject.secondary_invigilator_id:
                return JsonResponse({"status": "error", "message": "❌ คุณไม่ใช่ครูคุมสอบของวิชานี้"}, status=403)
            
            # อัปเดตสถานะและเวลาขึ้นอยู่กับตำแหน่ง
            if teacher.id == subject.invigilator_id:
                if new_status == "on_time":
                    subject.invigilator_checkin = True
                    subject.invigilator_checkin_time = now()
                else:
                    subject.invigilator_checkin = False
                    subject.invigilator_checkin_time = None
                position = "main"
            elif teacher.id == subject.secondary_invigilator_id:
                if new_status == "on_time":
                    subject.secondary_invigilator_checkin = True
                    subject.secondary_invigilator_checkin_time = now()
                else:
                    subject.secondary_invigilator_checkin = False
                    subject.secondary_invigilator_checkin_time = None
                position = "secondary"
            
            subject.save()
            return JsonResponse({"status": "success", "message": "✅ เช็คชื่อครูสำเร็จแล้ว!", "position": position})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"❌ เกิดข้อผิดพลาด: {str(e)}"}, status=500)
    return JsonResponse({"status": "error", "message": "❌ Method Not Allowed"}, status=405)



@login_required
def exam_subjects_teacher(request):
    user = request.user

    # ตรวจสอบว่าผู้ใช้เป็นครูจริง
    try:
        teacher_profile = TeacherProfile.objects.get(user=user)
    except TeacherProfile.DoesNotExist:
        return render(request, 'app/error.html', {'message': 'คุณไม่ได้เป็นครู'})

    # ดึงโรงเรียนของครู
    school_name = teacher_profile.user.school_name

    # ดึงระดับชั้นทั้งหมดที่เกี่ยวข้องกับวิชาที่ครูคุมสอบ (ทั้งหลักและรอง)
    all_classes = ExamSubject.objects.filter(
        Q(invigilator=teacher_profile) | Q(secondary_invigilator=teacher_profile)
    ).values_list("students__student_class", flat=True).distinct()

    # ตรวจสอบว่ามีการเลือกระดับชั้นไหม
    selected_class = request.GET.get("student_class", "all")

    # ดึงวิชาที่ครูคุมสอบโดยพิจารณาทั้งครูหลักและครูรอง
    subjects = ExamSubject.objects.filter(
        Q(invigilator=teacher_profile) | Q(secondary_invigilator=teacher_profile)
    )

    if selected_class != "all":
        subjects = subjects.filter(students__student_class=selected_class)

    subjects = subjects.distinct()

    # แปลงค่าระดับชั้นในแต่ละวิชาให้เป็น set (เพื่อลบค่าซ้ำ)
    for subject in subjects:
        subject.student_classes = set(subject.students.values_list('student_class', flat=True))

    return render(request, "app/teacher/exam_subjects_teacher.html", {
        "subjects": subjects,
        "all_classes": all_classes,
        "selected_class": selected_class,
        "school_name": school_name
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

@csrf_exempt
@login_required
def manual_teacher_checkin(request):
    """
    View สำหรับให้เจ้าหน้าที่อัปเดตสถานะการเช็คชื่อของครูผู้คุมสอบหลักหรือครูผู้คุมสอบสำรอง
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            teacher_id = data.get("teacher_id")
            subject_id = data.get("subject_id")
            status = data.get("status")  # คาดว่าจะเป็น "on_time" หรือ "absent"
            
            teacher = get_object_or_404(TeacherProfile, id=teacher_id)
            subject = get_object_or_404(ExamSubject, id=subject_id)

            # ตรวจสอบว่า teacher นี้เป็นครูคุมสอบหลักหรือสำรองของวิชานี้
            if teacher.id != subject.invigilator_id and teacher.id != subject.secondary_invigilator_id:
                return JsonResponse({"status": "error", "message": "❌ ครูนี้ไม่ใช่ครูคุมสอบของวิชานี้"}, status=403)

            # อัปเดตสถานะตามตำแหน่ง
            if teacher.id == subject.invigilator_id:
                subject.invigilator_checkin = True if status == "on_time" else False
                position = "main"
            else:
                subject.secondary_invigilator_checkin = True if status == "on_time" else False
                position = "secondary"
            subject.save()

            return JsonResponse({"status": "success", "position": position})
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "❌ ข้อมูล JSON ไม่ถูกต้อง"}, status=400)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"❌ เกิดข้อผิดพลาด: {str(e)}"}, status=500)

    return JsonResponse({"status": "error", "message": "❌ Method Not Allowed"}, status=405)

##################################################################################################################################################################
@login_required
def dashboard_student(request):
    if not request.user.is_student:
        return HttpResponseForbidden("เฉพาะนักเรียนเท่านั้น")
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    # ดึงตารางสอบสำหรับนักเรียนที่กำลังจะมาถึง (exam_date >= วันนี้)
    today = now().date()
    upcoming_exams = ExamSubject.objects.filter(students=student_profile, exam_date__gte=today).order_by('exam_date')
    
    # ดึงประวัติการสอบทั้งหมดสำหรับนักเรียนนี้
    exam_history = Attendance.objects.filter(student=student_profile).order_by('-checkin_time')
    
    context = {
        'upcoming_exams': upcoming_exams,
        'exam_history': exam_history,
    }
    return render(request, 'app/student/dashboard_student.html', context)

# 1. ดูตารางสอบและการลงทะเบียน
@login_required
def exam_schedule(request):
    if not request.user.is_student:
        return HttpResponseForbidden("เฉพาะนักเรียนเท่านั้น")
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    subjects = ExamSubject.objects.filter(students=student_profile).order_by('exam_date')
    
    # กำหนดเลขที่นั่งสอบให้กับแต่ละวิชา
    for subject in subjects:
        # ดึงรายชื่อนักเรียนในวิชานี้ โดยเรียงตามเกณฑ์ที่ต้องการ
        students = list(subject.students.order_by('student_class', 'user__last_name'))
        for idx, student in enumerate(students, start=1):
            if student.user.id == request.user.id:
                subject.seat_number = idx
                break
                
    return render(request, 'app/student/exam_schedule.html', {'subjects': subjects})


# 2. ประวัติการสอบ
@login_required
def exam_history(request):
    if not request.user.is_student:
        return HttpResponseForbidden("เฉพาะนักเรียนเท่านั้น")
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    attendance_records = Attendance.objects.filter(student=student_profile).order_by('-checkin_time')
    return render(request, 'app/student/exam_history.html', {'attendance_records': attendance_records})

# 3. ปรับปรุงโปรไฟล์ (นักเรียน)
@login_required
def update_profile(request):
    if not request.user.is_student:
        return HttpResponseForbidden("เฉพาะนักเรียนเท่านั้น")
    user_instance = request.user
    student_profile = get_object_or_404(StudentProfile, user=user_instance)
    if request.method == 'POST':
        user_form = UserProfileEditForm(request.POST, instance=user_instance)
        profile_form = StudentProfileEditForm(request.POST, instance=student_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "อัปเดตโปรไฟล์เรียบร้อยแล้ว")
            return redirect('dashboard_student')
        else:
            messages.error(request, "กรุณาตรวจสอบข้อมูลที่กรอก")
    else:
        user_form = UserProfileEditForm(instance=user_instance)
        profile_form = StudentProfileEditForm(instance=student_profile)
    return render(request, 'app/student/update_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

