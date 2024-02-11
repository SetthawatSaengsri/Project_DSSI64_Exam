# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *
from .models import *
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import qrcode
from io import BytesIO

def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student registration successful.')
            return redirect('success_page')
    else:
        form = StudentRegistrationForm()
    return render(request, 'app/register_student.html', {'form': form})

def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher registration successful.')
            return redirect('index_view')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'app/register_teacher.html', {'form': form})


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # ตรวจสอบประเภทของผู้ใช้และเปลี่ยนเส้นทางไปยังหน้าที่เหมาะสม
            if user.is_student:
                return redirect('dashboard_student')  # ตั้งชื่อ URL สำหรับหน้า dashboard ของนักเรียน
            elif user.is_teacher:
                return redirect('dashboard_teacher')  # ตั้งชื่อ URL สำหรับหน้า dashboard ของครู
            else:
                # ถ้าไม่ใช่ student หรือ teacher, กลับไปที่หน้าหลักหรือหน้าอื่น
                return redirect('index_view')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'app/login.html')


def logout_user(request):
    logout(request)
    return redirect('index_view')

def index_view(request):
    return render(request, 'app/index.html')

def success_page(request):
    return render(request, 'app/success_page.html')


@login_required
def dashboard_teacher(request):
    user = request.user
    return render(request, 'app/teacher/dashboard_teacher.html', {'user': user})

@login_required
def add_exam_subject(request):
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exam_subject_list')
    else:
        form = ExamSubjectForm()
    return render(request, 'app/teacher/add_exam_subject.html', {'form': form})

@login_required
# View to display the form for editing an exam subject
def edit_exam_subject(request, subject_id):
    subject = get_object_or_404(ExamSubject, id=subject_id)
    if request.method == 'POST':
        form = ExamSubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('exam_subject_list')
    else:
        form = ExamSubjectForm(instance=subject)
    return render(request, 'app/teacher/edit_subject.html', {'form': form})

@login_required
# View to update the exam subject details
def update_exam_subject(request):
    if request.method == "POST":
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(ExamSubject, id=subject_id)
        form = ExamSubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
    return redirect('exam_subject_list')

@login_required
def exam_subject_list(request):
    subjects = ExamSubject.objects.all()
    return render(request, 'app/teacher/exam_subject_list.html', {'subjects': subjects})

def class_students_list(request, student_class):
    # แปลง _ กลับเป็น / หากจำเป็น
    student_class = student_class.replace('_', '/')
    students = StudentProfile.objects.filter(student_class=student_class)
    return render(request, 'app/teacher/class_students_list.html', {
        'students': students,
        'student_class': student_class
    })  

@login_required
def generate_qr_code_for_exam(request, exam_subject_id):
    # ตรวจสอบว่า ExamSubject นั้นๆ มีอยู่จริง
    exam_subject = get_object_or_404(ExamSubject, id=exam_subject_id)

    # ตรวจสอบว่าผู้ใช้เป็นนักเรียนและอยู่ในชั้นเรียนที่เกี่ยวข้อง
    if request.user.is_student and request.user.student_profile.student_class == exam_subject.student_class.student_class:
        # สร้างข้อมูลสำหรับ QR Code
        data = f"Exam Details: {exam_subject.subject_name}, Room: {exam_subject.exam_room.name}, Date: {exam_subject.start_time.strftime('%Y-%m-%d %H:%M')} to {exam_subject.end_time.strftime('%Y-%m-%d %H:%M')}"
        
        # สร้าง QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # บันทึก QR Code เป็น BytesIO และส่งกลับเป็น image
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return HttpResponse(buffer.getvalue(), content_type="image/png")
    else:
        return 
# ตัวอย่างการส่ง exam_subject ไปยัง template
def qrcode_student(request):
    user = request.user
    exam_subjects = ExamSubject.objects.filter(student_class=user.student_profile.student_class) # ตัวอย่างการ filter exam subjects ตาม class ของนักเรียน
    return render(request, 'app/student/qr_code.html', {'exam_subjects': exam_subjects})


def dashboard_student(request):
    user = request.user
    return render(request, 'app/student/dashboard_student.html', {'user': user})

def edit_student(request):
    user = request.user
    return render(request, 'app/student/edit_profilestudent.html', {'user': user})

def Examination_history(request):
    user = request.user
    return render(request, 'app/student/Examination_history.html', {'user': user})

def qrcode_student(request):
    user = request.user
    return render(request, 'app/student/qr_code.html', {'user': user})

def dashboard_unknown(request):
    user = request.user
    return HttpResponse(f"Welcome, {user.first_name} {user.last_name} (Unknown User) - {user.username}")

