import os
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import and_
from app import db
from models import User, Student, Teacher, Room, Course, Enrollment, Schedule, Payment, Material, ExperimentalClass
from forms import *
from utils import send_email, allowed_file

# Create blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
admin = Blueprint('admin', __name__, url_prefix='/admin')
student_bp = Blueprint('student', __name__, url_prefix='/student')
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')
public = Blueprint('public', __name__, url_prefix='/public')

def register_blueprints(app):
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(public)

# Main routes
@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.user_type == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.user_type == 'student':
            return redirect(url_for('student.student_dashboard'))
        elif current_user.user_type == 'teacher':
            return redirect(url_for('teacher.teacher_dashboard'))
        else:
            return redirect(url_for('admin.dashboard'))
    return redirect(url_for('public.landing'))

# Authentication routes
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active and form.password.data and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            return redirect(next_page)
        flash('E-mail ou senha inválidos.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.landing'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = UserForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data or '123456'),
            user_type=form.user_type.data,
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

# Admin routes
@admin.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    # Dashboard statistics
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_courses = Course.query.filter_by(is_active=True).count()
    pending_payments = Payment.query.filter_by(status='pending').count()
    
    return render_template('admin/dashboard.html', 
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_courses=total_courses,
                         pending_payments=pending_payments)

@admin.route('/students')
@login_required
def students():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    students = db.session.query(Student, User).join(User, Student.user_id == User.id).all()
    return render_template('admin/students.html', students=students)

@admin.route('/student/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = StudentForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('admin/student_form.html', form=form, title='Adicionar Aluno')
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data or '123456'),
            user_type='student',
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        db.session.add(user)
        db.session.flush()
        
        # Create student profile
        student = Student(
            user_id=user.id,
            birth_date=form.birth_date.data,
            address=form.address.data,
            emergency_contact=form.emergency_contact.data,
            emergency_phone=form.emergency_phone.data,
            guardian_name=form.guardian_name.data,
            guardian_phone=form.guardian_phone.data,
            guardian_email=form.guardian_email.data,
            medical_info=form.medical_info.data,
            notes=form.notes.data
        )
        db.session.add(student)
        db.session.commit()
        
        flash('Aluno adicionado com sucesso!', 'success')
        return redirect(url_for('admin.students'))
    
    return render_template('admin/student_form.html', form=form, title='Adicionar Aluno')

@admin.route('/student/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.get_or_404(student_id)
    user = User.query.get_or_404(student.user_id)
    
    form = StudentForm(obj=student)
    # Populate form with user data
    form.username.data = user.username
    form.email.data = user.email
    form.full_name.data = user.full_name
    form.phone.data = user.phone
    
    if form.validate_on_submit():
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        # Update student profile
        student.birth_date = form.birth_date.data
        student.address = form.address.data
        student.emergency_contact = form.emergency_contact.data
        student.emergency_phone = form.emergency_phone.data
        student.guardian_name = form.guardian_name.data
        student.guardian_phone = form.guardian_phone.data
        student.guardian_email = form.guardian_email.data
        student.medical_info = form.medical_info.data
        student.notes = form.notes.data
        
        db.session.commit()
        flash('Aluno atualizado com sucesso!', 'success')
        return redirect(url_for('admin.students'))
    
    return render_template('admin/student_form.html', form=form, title='Editar Aluno')

@admin.route('/student/view/<int:student_id>')
@login_required
def view_student(student_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.get_or_404(student_id)
    user = User.query.get_or_404(student.user_id)
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.due_date.desc()).all()
    
    return render_template('admin/student_detail.html', student=student, user=user, 
                         enrollments=enrollments, payments=payments)

@admin.route('/student/toggle/<int:student_id>')
@login_required
def toggle_student(student_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.get_or_404(student_id)
    user = User.query.get_or_404(student.user_id)
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'ativado' if user.is_active else 'desativado'
    flash(f'Aluno {status} com sucesso!', 'success')
    return redirect(url_for('admin.students'))

@admin.route('/teachers')
@login_required
def teachers():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teachers = db.session.query(Teacher, User).join(User, Teacher.user_id == User.id).all()
    return render_template('admin/teachers.html', teachers=teachers)

@admin.route('/teacher/add', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = TeacherForm()
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Este e-mail já está cadastrado.', 'danger')
            return render_template('admin/teacher_form.html', form=form, title='Adicionar Professor')
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data or '123456'),
            user_type='teacher',
            full_name=form.full_name.data,
            phone=form.phone.data
        )
        db.session.add(user)
        db.session.flush()
        
        # Create teacher profile
        teacher = Teacher(
            user_id=user.id,
            specialization=form.specialization.data,
            hourly_rate=form.hourly_rate.data,
            bank_name=form.bank_name.data,
            bank_agency=form.bank_agency.data,
            bank_account=form.bank_account.data,
            pix_key=form.pix_key.data,
            bio=form.bio.data,
            qualifications=form.qualifications.data
        )
        db.session.add(teacher)
        db.session.commit()
        
        flash('Professor adicionado com sucesso!', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/teacher_form.html', form=form, title='Adicionar Professor')

@admin.route('/teacher/edit/<int:teacher_id>', methods=['GET', 'POST'])
@login_required
def edit_teacher(teacher_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get_or_404(teacher.user_id)
    
    form = TeacherForm(obj=teacher)
    # Populate form with user data
    form.username.data = user.username
    form.email.data = user.email
    form.full_name.data = user.full_name
    form.phone.data = user.phone
    
    if form.validate_on_submit():
        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.phone = form.phone.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        
        # Update teacher profile
        teacher.specialization = form.specialization.data
        teacher.hourly_rate = form.hourly_rate.data
        teacher.bank_name = form.bank_name.data
        teacher.bank_agency = form.bank_agency.data
        teacher.bank_account = form.bank_account.data
        teacher.pix_key = form.pix_key.data
        teacher.bio = form.bio.data
        teacher.qualifications = form.qualifications.data
        
        db.session.commit()
        flash('Professor atualizado com sucesso!', 'success')
        return redirect(url_for('admin.teachers'))
    
    return render_template('admin/teacher_form.html', form=form, title='Editar Professor')

@admin.route('/teacher/view/<int:teacher_id>')
@login_required
def view_teacher(teacher_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get_or_404(teacher.user_id)
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    schedules = Schedule.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('admin/teacher_detail.html', teacher=teacher, user=user,
                         courses=courses, schedules=schedules)


@admin.route('/rooms')
@login_required
def rooms():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@admin.route('/room/add', methods=['GET', 'POST'])
@login_required
def add_room():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = RoomForm()
    if form.validate_on_submit():
        room = Room(
            name=form.name.data,
            capacity=form.capacity.data,
            equipment=form.equipment.data,
            location=form.location.data,
            is_available=form.is_available.data,
            notes=form.notes.data
        )
        db.session.add(room)
        db.session.commit()
        
        flash('Sala adicionada com sucesso!', 'success')
        return redirect(url_for('admin.rooms'))
    
    return render_template('admin/room_form.html', form=form, title='Adicionar Sala')

@admin.route('/room/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_room(room_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    room = Room.query.get_or_404(room_id)
    form = RoomForm(obj=room)
    
    if form.validate_on_submit():
        room.name = form.name.data
        room.capacity = form.capacity.data
        room.equipment = form.equipment.data
        room.location = form.location.data
        room.is_available = form.is_available.data
        room.notes = form.notes.data
        
        db.session.commit()
        flash('Sala atualizada com sucesso!', 'success')
        return redirect(url_for('admin.rooms'))
    
    return render_template('admin/room_form.html', form=form, title='Editar Sala')

@admin.route('/room/view/<int:room_id>')
@login_required
def view_room(room_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    room = Room.query.get_or_404(room_id)
    schedules = db.session.query(Schedule, Course, Teacher, User).join(Course, Schedule.course_id == Course.id).join(Teacher, Schedule.teacher_id == Teacher.id).join(User, Teacher.user_id == User.id).filter(Schedule.room_id == room.id).all()
    
    return render_template('admin/room_detail.html', room=room, schedules=schedules)

@admin.route('/courses')
@login_required
def courses():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    courses = db.session.query(Course, Teacher, User).outerjoin(Teacher, Course.teacher_id == Teacher.id).outerjoin(User, Teacher.user_id == User.id).all()
    return render_template('admin/courses.html', courses=courses)

@admin.route('/course/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = CourseForm()
    # Populate teacher choices
    teachers = db.session.query(Teacher, User).join(User, Teacher.user_id == User.id).all()
    form.teacher_id.choices = [('0', 'Selecione um professor')] + [(str(t.Teacher.id), t.User.full_name) for t in teachers]
    
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            description=form.description.data,
            instrument=form.instrument.data,
            level=form.level.data,
            duration_months=form.duration_months.data,
            monthly_price=form.monthly_price.data,
            max_students=form.max_students.data,
            teacher_id=int(form.teacher_id.data) if form.teacher_id.data != '0' else None,
            is_active=form.is_active.data
        )
        db.session.add(course)
        db.session.commit()
        
        flash('Curso adicionado com sucesso!', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/course_form.html', form=form, title='Adicionar Curso')

@admin.route('/course/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    
    # Populate teacher choices
    teachers = db.session.query(Teacher, User).join(User, Teacher.user_id == User.id).all()
    form.teacher_id.choices = [('0', 'Selecione um professor')] + [(str(t.Teacher.id), t.User.full_name) for t in teachers]
    
    if course.teacher_id:
        form.teacher_id.data = str(course.teacher_id)
    
    if form.validate_on_submit():
        course.name = form.name.data
        course.description = form.description.data
        course.instrument = form.instrument.data
        course.level = form.level.data
        course.duration_months = form.duration_months.data
        course.monthly_price = form.monthly_price.data
        course.max_students = form.max_students.data
        course.teacher_id = int(form.teacher_id.data) if form.teacher_id.data != '0' else None
        course.is_active = form.is_active.data
        
        db.session.commit()
        flash('Curso atualizado com sucesso!', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/course_form.html', form=form, title='Editar Curso')


@admin.route('/schedule')
@login_required
def schedule():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    schedules = db.session.query(Schedule, Course, Teacher, User, Room).join(Course, Schedule.course_id == Course.id).join(Teacher, Schedule.teacher_id == Teacher.id).join(User, Teacher.user_id == User.id).join(Room, Schedule.room_id == Room.id).all()
    return render_template('admin/schedule.html', schedules=schedules)

@admin.route('/schedule/add', methods=['GET', 'POST'])
@login_required
def add_schedule():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = ScheduleForm()
    
    # Populate choices
    courses = Course.query.filter_by(is_active=True).all()
    teachers = db.session.query(Teacher, User).join(User, Teacher.user_id == User.id).all()
    rooms = Room.query.filter_by(is_available=True).all()
    
    form.course_id.choices = [(0, 'Selecione um curso')] + [(c.id, c.name) for c in courses]
    form.teacher_id.choices = [(0, 'Selecione um professor')] + [(t.Teacher.id, t.User.full_name) for t in teachers]
    form.room_id.choices = [(0, 'Selecione uma sala')] + [(r.id, r.name) for r in rooms]
    
    if form.validate_on_submit():
        schedule = Schedule()
        schedule.course_id = form.course_id.data
        schedule.teacher_id = form.teacher_id.data
        schedule.room_id = form.room_id.data
        schedule.day_of_week = form.day_of_week.data
        schedule.start_time = form.start_time.data
        schedule.end_time = form.end_time.data
        schedule.is_active = True
        db.session.add(schedule)
        db.session.commit()
        
        flash('Horário adicionado com sucesso!', 'success')
        return redirect(url_for('admin.schedule'))
    
    return render_template('admin/schedule_form.html', form=form, title='Adicionar Horário')

@admin.route('/schedule/edit/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    form = ScheduleForm(obj=schedule)
    
    # Populate choices
    courses = Course.query.filter_by(is_active=True).all()
    teachers = db.session.query(Teacher, User).join(User, Teacher.user_id == User.id).all()
    rooms = Room.query.filter_by(is_available=True).all()
    
    form.course_id.choices = [(0, 'Selecione um curso')] + [(c.id, c.name) for c in courses]
    form.teacher_id.choices = [(0, 'Selecione um professor')] + [(t.Teacher.id, t.User.full_name) for t in teachers]
    form.room_id.choices = [(0, 'Selecione uma sala')] + [(r.id, r.name) for r in rooms]
    
    if form.validate_on_submit():
        schedule.course_id = form.course_id.data
        schedule.teacher_id = form.teacher_id.data
        schedule.room_id = form.room_id.data
        schedule.day_of_week = form.day_of_week.data
        schedule.start_time = form.start_time.data
        schedule.end_time = form.end_time.data
        
        db.session.commit()
        flash('Horário atualizado com sucesso!', 'success')
        return redirect(url_for('admin.schedule'))
    
    return render_template('admin/schedule_form.html', form=form, title='Editar Horário')

@admin.route('/schedule/delete/<int:schedule_id>')
@login_required
def delete_schedule(schedule_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    schedule.is_active = False
    db.session.commit()
    
    flash('Horário removido com sucesso!', 'success')
    return redirect(url_for('admin.schedule'))

@admin.route('/finances')
@login_required
def finances():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    payments = db.session.query(Payment, Student, User).join(Student, Payment.student_id == Student.id).join(User, Student.user_id == User.id).all()
    return render_template('admin/finances.html', payments=payments)

@admin.route('/payment/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = PaymentForm()
    
    # Populate student choices
    students = db.session.query(Student, User).join(User, Student.user_id == User.id).all()
    form.student_id.choices = [(0, 'Selecione um aluno')] + [(s.Student.id, s.User.full_name) for s in students]
    
    if form.validate_on_submit():
        payment = Payment()
        payment.student_id = form.student_id.data
        payment.amount = form.amount.data
        payment.due_date = form.due_date.data
        payment.payment_date = form.payment_date.data
        payment.status = form.status.data
        payment.payment_method = form.payment_method.data
        payment.reference_month = form.reference_month.data
        payment.notes = form.notes.data
        db.session.add(payment)
        db.session.commit()
        
        flash('Pagamento registrado com sucesso!', 'success')
        return redirect(url_for('admin.finances'))
    
    return render_template('admin/payment_form.html', form=form, title='Registrar Pagamento')

@admin.route('/payment/edit/<int:payment_id>', methods=['GET', 'POST'])
@login_required
def edit_payment(payment_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.get_or_404(payment_id)
    form = PaymentForm(obj=payment)
    
    # Populate student choices
    students = db.session.query(Student, User).join(User, Student.user_id == User.id).all()
    form.student_id.choices = [(0, 'Selecione um aluno')] + [(s.Student.id, s.User.full_name) for s in students]
    
    if form.validate_on_submit():
        payment.student_id = form.student_id.data
        payment.amount = form.amount.data
        payment.due_date = form.due_date.data
        payment.payment_date = form.payment_date.data
        payment.status = form.status.data
        payment.payment_method = form.payment_method.data
        payment.reference_month = form.reference_month.data
        payment.notes = form.notes.data
        
        db.session.commit()
        flash('Pagamento atualizado com sucesso!', 'success')
        return redirect(url_for('admin.finances'))
    
    return render_template('admin/payment_form.html', form=form, title='Editar Pagamento')

@admin.route('/payment/mark-paid/<int:payment_id>')
@login_required
def mark_payment_paid(payment_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.get_or_404(payment_id)
    payment.status = 'paid'
    payment.payment_date = datetime.now().date()
    db.session.commit()
    
    flash('Pagamento marcado como pago!', 'success')
    return redirect(url_for('admin.finances'))

@admin.route('/payment/view/<int:payment_id>')
@login_required
def view_payment(payment_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.get_or_404(payment_id)
    student = Student.query.get_or_404(payment.student_id)
    user = User.query.get_or_404(student.user_id)
    
    return render_template('admin/payment_detail.html', payment=payment, student=student, user=user)

# Student routes
@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.user_type != 'student':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Perfil de aluno não encontrado.', 'danger')
        return redirect(url_for('main.index'))
    
    enrollments = Enrollment.query.filter_by(student_id=student.id).all()
    recent_payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html', 
                         student=student,
                         enrollments=enrollments,
                         recent_payments=recent_payments)

@student_bp.route('/materials')
@login_required
def materials():
    if current_user.user_type != 'student':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Perfil de aluno não encontrado.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get courses the student is enrolled in
    enrolled_courses = db.session.query(Course).join(Enrollment).filter(Enrollment.student_id == student.id).all()
    course_ids = [course.id for course in enrolled_courses]
    
    # Get materials for these courses
    materials = Material.query.filter(Material.course_id.in_(course_ids)).all()
    
    return render_template('student/materials.html', materials=materials, courses=enrolled_courses)

# Teacher routes
@teacher_bp.route('/dashboard')
@login_required
def teacher_dashboard():
    if current_user.user_type != 'teacher':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher:
        flash('Perfil de professor não encontrado.', 'danger')
        return redirect(url_for('main.index'))
    
    courses = Course.query.filter_by(teacher_id=teacher.id).all()
    schedules = Schedule.query.filter_by(teacher_id=teacher.id).all()
    
    return render_template('teacher/dashboard.html', 
                         teacher=teacher,
                         courses=courses,
                         schedules=schedules)

# Public routes
@public.route('/')
def landing():
    return render_template('public/landing.html')

@public.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Send email notification
        try:
            send_email(
                subject=f'Contato do site: {form.subject.data}',
                body=f'''
                Nome: {form.name.data}
                E-mail: {form.email.data}
                Telefone: {form.phone.data}
                
                Mensagem:
                {form.message.data}
                ''',
                recipients=['admin@solmaior.com']
            )
            flash('Mensagem enviada com sucesso! Entraremos em contato em breve.', 'success')
        except Exception as e:
            current_app.logger.error(f'Error sending contact email: {e}')
            flash('Erro ao enviar mensagem. Tente novamente.', 'danger')
        
        return redirect(url_for('public.contact'))
    
    return render_template('public/contact.html', form=form)

@public.route('/experimental-class', methods=['GET', 'POST'])
def experimental_class():
    form = ExperimentalClassForm()
    if form.validate_on_submit():
        experimental_class = ExperimentalClass(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            instrument=form.instrument.data,
            experience_level=form.experience_level.data,
            preferred_date=form.preferred_date.data,
            preferred_time=form.preferred_time.data,
            notes=form.notes.data
        )
        db.session.add(experimental_class)
        db.session.commit()
        
        # Send notification email
        try:
            send_email(
                subject='Nova solicitação de aula experimental',
                body=f'''
                Nome: {form.name.data}
                E-mail: {form.email.data}
                Telefone: {form.phone.data}
                Instrumento: {form.instrument.data}
                Experiência: {form.experience_level.data}
                Data preferencial: {form.preferred_date.data}
                Horário preferencial: {form.preferred_time.data}
                
                Observações:
                {form.notes.data}
                ''',
                recipients=['admin@solmaior.com']
            )
        except Exception as e:
            current_app.logger.error(f'Error sending experimental class email: {e}')
        
        flash('Solicitação de aula experimental enviada com sucesso! Entraremos em contato em breve.', 'success')
        return redirect(url_for('public.experimental_class'))
    
    return render_template('public/experimental_class.html', form=form)

# File upload route
@main.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Payment Gateway Routes
@admin.route('/payment/<int:payment_id>/create-pix')
@login_required
def create_pix_payment(payment_id):
    if current_user.user_type not in ['admin', 'secretary']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    payment = Payment.query.get_or_404(payment_id)
    student = Student.query.get(payment.student_id)
    user = User.query.get(student.user_id)
    
    from payment_gateway import PaymentGateway
    gateway = PaymentGateway()
    
    payer_info = {
        'name': user.full_name,
        'email': user.email,
        'document': ''  # CPF se disponível
    }
    
    result = gateway.create_pix_payment(
        payment_id=payment.id,
        amount=payment.amount,
        description=f"Mensalidade {payment.reference_month.strftime('%m/%Y')}",
        payer_info=payer_info
    )
    
    if result['success']:
        from models import PaymentTransaction
        
        # Criar registro da transação
        transaction = PaymentTransaction()
        transaction.payment_id = payment.id
        transaction.transaction_id = result['transaction_id']
        transaction.payment_method = 'PIX'
        transaction.amount = payment.amount
        transaction.pix_code = result['pix_code']
        transaction.pix_qr_code = result['pix_qr_code']
        transaction.expires_at = datetime.strptime(result['expires_at'], '%Y-%m-%dT%H:%M:%S')
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'pix_code': result['pix_code'],
            'qr_code': result['pix_qr_code'],
            'expires_at': result['expires_at']
        })
    else:
        return jsonify({'success': False, 'error': result['error']})

@student_bp.route('/payment/<int:payment_id>/pay')
@login_required
def pay_online(payment_id):
    if current_user.user_type != 'student':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Perfil de aluno não encontrado.', 'danger')
        return redirect(url_for('main.index'))
    
    payment = Payment.query.filter_by(id=payment_id, student_id=student.id).first()
    if not payment:
        flash('Pagamento não encontrado.', 'danger')
        return redirect(url_for('student.student_dashboard'))
    
    if payment.status == 'paid':
        flash('Pagamento já foi realizado.', 'info')
        return redirect(url_for('student.student_dashboard'))
    
    return render_template('student/payment_online.html', payment=payment)

@main.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """
    Webhook para receber notificações do gateway de pagamento
    """
    try:
        data = request.get_json()
        
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        paid_amount = data.get('amount')
        
        from payment_gateway import PaymentProcessor
        
        success = PaymentProcessor.process_payment_confirmation(
            transaction_id=transaction_id,
            status=status,
            paid_amount=paid_amount
        )
        
        if success:
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'status': 'error'}), 400
            
    except Exception as e:
        current_app.logger.error(f'Webhook error: {e}')
        return jsonify({'status': 'error'}), 500

@admin.route('/send-payment-reminders', methods=['POST'])
@login_required
def send_payment_reminders():
    if current_user.user_type not in ['admin', 'secretary']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    from notification_service import NotificationService
    
    try:
        results = NotificationService.check_and_send_payment_reminders()
        
        return jsonify({
            'success': True,
            'warning_sent': results['warning_sent'],
            'overdue_sent': results['overdue_sent'],
            'message': f"Enviados {results['warning_sent']} avisos e {results['overdue_sent']} cobranças"
        })
        
    except Exception as e:
        current_app.logger.error(f'Error sending reminders: {e}')
        return jsonify({'error': 'Erro ao enviar lembretes'}), 500

# Additional admin routes for course management
@admin.route('/course/<int:course_id>')
@login_required
def view_course(course_id):
    if current_user.user_type not in ['admin', 'secretary', 'teacher']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Get enrollments with student and user data
    enrollments = db.session.query(Enrollment, Student, User).join(
        Student, Enrollment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).filter(Enrollment.course_id == course_id).all()
    
    # Get course materials
    materials = Material.query.filter_by(course_id=course_id).all()
    
    # Get course schedules
    schedules = Schedule.query.filter_by(course_id=course_id).all()
    
    return render_template('admin/course_detail.html', 
                         course=course, 
                         enrollments=enrollments,
                         materials=materials,
                         schedules=schedules)

@admin.route('/course/<int:course_id>/students')
@login_required
def course_students(course_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Get enrollments with student and user data
    enrollments = db.session.query(Enrollment, Student, User).join(
        Student, Enrollment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).filter(Enrollment.course_id == course_id).all()
    
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('admin/course_students.html', 
                         course=course, 
                         enrollments=enrollments,
                         today=today)

@admin.route('/course/<int:course_id>/materials')
@login_required
def course_materials(course_id):
    if current_user.user_type not in ['admin', 'secretary', 'teacher']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check if teacher is accessing their own course
    if current_user.user_type == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher or course.teacher_id != teacher.id:
            flash('Você só pode acessar materiais dos seus próprios cursos.', 'danger')
            return redirect(url_for('teacher.teacher_dashboard'))
    
    # Get course materials with uploader info
    materials = db.session.query(Material, User).outerjoin(
        User, Material.uploaded_by_id == User.id
    ).filter(Material.course_id == course_id).order_by(Material.uploaded_at.desc()).all()
    
    return render_template('admin/course_materials.html', 
                         course=course, 
                         materials=[m.Material for m, u in materials])

@admin.route('/teacher/<int:teacher_id>/schedule')
@login_required
def teacher_schedule(teacher_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teacher = Teacher.query.get_or_404(teacher_id)
    user = User.query.get(teacher.user_id)
    
    # Get teacher's schedules with course and room info
    schedules = db.session.query(Schedule, Course, Room).join(
        Course, Schedule.course_id == Course.id
    ).outerjoin(
        Room, Schedule.room_id == Room.id
    ).filter(Schedule.teacher_id == teacher_id).order_by(
        Schedule.day_of_week, Schedule.start_time
    ).all()
    
    return render_template('admin/teacher_schedule.html', 
                         teacher=teacher, 
                         user=user,
                         schedules=schedules)

# API Routes for AJAX calls
@admin.route('/api/available-students/<int:course_id>')
@login_required
def api_available_students(course_id):
    if current_user.user_type not in ['admin', 'secretary']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    # Get students not enrolled in this course
    enrolled_students = db.session.query(Student.id).join(Enrollment).filter(
        Enrollment.course_id == course_id,
        Enrollment.status.in_(['active', 'suspended'])
    ).subquery()
    
    available_students = db.session.query(Student, User).join(User).filter(
        ~Student.id.in_(enrolled_students),
        User.is_active == True
    ).all()
    
    students_data = [
        {'id': student.id, 'name': user.full_name, 'email': user.email}
        for student, user in available_students
    ]
    
    return jsonify({'students': students_data})

@admin.route('/enrollment/<int:enrollment_id>/status', methods=['POST'])
@login_required
def change_enrollment_status(enrollment_id):
    if current_user.user_type not in ['admin', 'secretary']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['active', 'suspended', 'cancelled', 'completed']:
        return jsonify({'error': 'Status inválido'}), 400
    
    enrollment.status = new_status
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Status alterado para {new_status}'})

@admin.route('/course/<int:course_id>/enroll', methods=['POST'])
@login_required
def enroll_student(course_id):
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    student_id = request.form.get('student_id')
    enrollment_date = request.form.get('enrollment_date')
    discount_percentage = request.form.get('discount_percentage', 0)
    
    if not student_id or not enrollment_date:
        flash('Dados incompletos.', 'danger')
        return redirect(url_for('admin.course_students', course_id=course_id))
    
    # Check if student is already enrolled
    existing = Enrollment.query.filter_by(
        student_id=student_id,
        course_id=course_id,
        status='active'
    ).first()
    
    if existing:
        flash('Aluno já está matriculado neste curso.', 'warning')
        return redirect(url_for('admin.course_students', course_id=course_id))
    
    # Check course capacity
    active_enrollments = Enrollment.query.filter_by(
        course_id=course_id,
        status='active'
    ).count()
    
    if active_enrollments >= course.max_students:
        flash('Curso já atingiu a capacidade máxima.', 'warning')
        return redirect(url_for('admin.course_students', course_id=course_id))
    
    # Calculate monthly payment with discount
    monthly_payment = course.monthly_price
    if discount_percentage and float(discount_percentage) > 0:
        discount = float(discount_percentage) / 100
        monthly_payment = course.monthly_price * (1 - discount)
    
    # Create enrollment
    enrollment = Enrollment()
    enrollment.student_id = student_id
    enrollment.course_id = course_id
    enrollment.enrollment_date = datetime.strptime(enrollment_date, '%Y-%m-%d').date()
    enrollment.status = 'active'
    enrollment.discount_percentage = discount_percentage
    enrollment.monthly_payment = monthly_payment
    
    db.session.add(enrollment)
    db.session.commit()
    
    flash('Aluno matriculado com sucesso!', 'success')
    return redirect(url_for('admin.course_students', course_id=course_id))

@admin.route('/quick-enroll', methods=['GET', 'POST'])
@login_required
def quick_enroll():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        enrollment_date = request.form.get('enrollment_date')
        discount_percentage = request.form.get('discount_percentage', 0)
        
        if not student_id or not course_id or not enrollment_date:
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('admin.quick_enroll'))
        
        # Verify student and course exist
        student = Student.query.get(student_id)
        course = Course.query.get(course_id)
        
        if not student or not course:
            flash('Aluno ou curso não encontrado.', 'danger')
            return redirect(url_for('admin.quick_enroll'))
        
        # Check if already enrolled
        existing = Enrollment.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            status='active'
        ).first()
        
        if existing:
            flash('Aluno já está matriculado neste curso.', 'warning')
            return redirect(url_for('admin.quick_enroll'))
        
        # Check course capacity
        active_enrollments = Enrollment.query.filter_by(
            course_id=course_id,
            status='active'
        ).count()
        
        if active_enrollments >= course.max_students:
            flash('Curso já atingiu a capacidade máxima.', 'warning')
            return redirect(url_for('admin.quick_enroll'))
        
        # Calculate monthly payment with discount
        monthly_payment = course.monthly_price
        if discount_percentage and float(discount_percentage) > 0:
            discount = float(discount_percentage) / 100
            monthly_payment = course.monthly_price * (1 - discount)
        
        # Create enrollment
        enrollment = Enrollment()
        enrollment.student_id = student_id
        enrollment.course_id = course_id
        enrollment.enrollment_date = datetime.strptime(enrollment_date, '%Y-%m-%d').date()
        enrollment.status = 'active'
        enrollment.discount_percentage = discount_percentage
        enrollment.monthly_payment = monthly_payment
        
        db.session.add(enrollment)
        db.session.commit()
        
        flash('Matrícula realizada com sucesso!', 'success')
        return redirect(url_for('admin.view_student', student_id=student_id))
    
    # GET request - show form
    students = db.session.query(Student, User).join(User, Student.user_id == User.id).filter(User.is_active == True).all()
    courses = Course.query.filter_by(is_active=True).all()
    
    return render_template('admin/quick_enroll.html', students=students, courses=courses)

@admin.route('/reports')
@login_required
def reports():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from sqlalchemy import func, extract
    
    # Estatísticas gerais
    total_students = Student.query.count()
    active_students = db.session.query(Student).join(User).filter(User.is_active == True).count()
    inactive_students = total_students - active_students
    
    total_courses = Course.query.filter_by(is_active=True).count()
    total_teachers = Teacher.query.count()
    
    # Alunos sem matrícula ativa
    students_without_enrollment = db.session.query(Student, User).join(
        User, Student.user_id == User.id
    ).outerjoin(
        Enrollment, and_(Enrollment.student_id == Student.id, Enrollment.status == 'active')
    ).filter(
        Enrollment.id == None,
        User.is_active == True
    ).all()
    
    # Cursos sem professor
    courses_without_teacher = Course.query.filter(
        Course.teacher_id == None,
        Course.is_active == True
    ).all()
    
    # Análise de inadimplência
    today = datetime.now().date()
    pending_payments = db.session.query(Payment, Student, User).join(
        Student, Payment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).filter(Payment.status == 'pending').all()
    
    overdue_payments = db.session.query(Payment, Student, User).join(
        Student, Payment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).filter(
        Payment.status.in_(['pending', 'overdue']),
        Payment.due_date < today
    ).all()
    
    # Taxa de inadimplência
    total_payments = Payment.query.count()
    overdue_count = len(overdue_payments)
    default_rate = (overdue_count / total_payments * 100) if total_payments > 0 else 0
    
    # Receita mensal
    current_month_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'paid',
        extract('month', Payment.payment_date) == datetime.now().month,
        extract('year', Payment.payment_date) == datetime.now().year
    ).scalar() or 0
    
    # Receita perdida por inadimplência
    lost_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status.in_(['pending', 'overdue']),
        Payment.due_date < today
    ).scalar() or 0
    
    # Matrículas por curso com detalhes financeiros
    enrollment_stats = db.session.query(
        Course.name,
        Course.monthly_price,
        func.count(Enrollment.id).label('total_enrollments'),
        func.sum(Course.monthly_price).label('potential_revenue')
    ).join(
        Enrollment, Course.id == Enrollment.course_id
    ).filter(
        Enrollment.status == 'active'
    ).group_by(Course.id, Course.name, Course.monthly_price).all()
    
    # Análise de crescimento (últimos 12 meses)
    growth_data = []
    for i in range(12):
        target_date = datetime.now() - timedelta(days=30*i)
        enrollments_count = Enrollment.query.filter(
            extract('month', Enrollment.enrollment_date) == target_date.month,
            extract('year', Enrollment.enrollment_date) == target_date.year
        ).count()
        growth_data.append({
            'month': target_date.strftime('%m/%Y'),
            'enrollments': enrollments_count
        })
    
    # Top 5 alunos inadimplentes
    top_defaulters = db.session.query(
        User.full_name,
        func.sum(Payment.amount).label('total_debt'),
        func.count(Payment.id).label('overdue_count')
    ).join(
        Student, User.id == Student.user_id
    ).join(
        Payment, Student.id == Payment.student_id
    ).filter(
        Payment.status.in_(['pending', 'overdue']),
        Payment.due_date < today
    ).group_by(User.id, User.full_name).order_by(
        func.sum(Payment.amount).desc()
    ).limit(5).all()
    
    return render_template('admin/reports.html',
                         total_students=total_students,
                         active_students=active_students,
                         inactive_students=inactive_students,
                         total_courses=total_courses,
                         total_teachers=total_teachers,
                         students_without_enrollment=students_without_enrollment,
                         courses_without_teacher=courses_without_teacher,
                         pending_payments=pending_payments,
                         overdue_payments=overdue_payments,
                         default_rate=default_rate,
                         current_month_revenue=current_month_revenue,
                         lost_revenue=lost_revenue,
                         enrollment_stats=enrollment_stats,
                         growth_data=growth_data,
                         top_defaulters=top_defaulters)

@admin.route('/financial-summary')
@login_required
def financial_summary():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    from sqlalchemy import func, extract
    
    # Receita por mês (últimos 12 meses)
    monthly_revenue = db.session.query(
        extract('year', Payment.payment_date).label('year'),
        extract('month', Payment.payment_date).label('month'),
        func.sum(Payment.amount).label('total')
    ).filter(
        Payment.status == 'paid',
        Payment.payment_date >= datetime.now().replace(year=datetime.now().year-1)
    ).group_by(
        extract('year', Payment.payment_date),
        extract('month', Payment.payment_date)
    ).order_by('year', 'month').all()
    
    # Inadimplência
    overdue_payments = db.session.query(Payment, Student, User).join(
        Student, Payment.student_id == Student.id
    ).join(
        User, Student.user_id == User.id
    ).filter(
        Payment.status == 'pending',
        Payment.due_date < datetime.now().date()
    ).all()
    
    overdue_amount = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'pending',
        Payment.due_date < datetime.now().date()
    ).scalar() or 0
    
    # Receita por curso
    course_revenue = db.session.query(
        Course.name,
        func.sum(Payment.amount).label('total_revenue')
    ).join(
        Enrollment, Course.id == Enrollment.course_id
    ).join(
        Payment, Enrollment.student_id == Payment.student_id
    ).filter(
        Payment.status == 'paid'
    ).group_by(Course.id, Course.name).all()
    
    return render_template('admin/financial_summary.html',
                         monthly_revenue=monthly_revenue,
                         overdue_payments=overdue_payments,
                         overdue_amount=overdue_amount,
                         course_revenue=course_revenue)

@admin.route('/material/<int:material_id>/download')
@login_required
def download_material(material_id):
    if current_user.user_type not in ['admin', 'secretary', 'teacher', 'student']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    material = Material.query.get_or_404(material_id)
    
    # Check if user has access to this material
    if current_user.user_type == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Perfil de estudante não encontrado.', 'danger')
            return redirect(url_for('main.index'))
        
        # Check if student is enrolled in the course
        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=material.course_id,
            status='active'
        ).first()
        
        if not enrollment:
            flash('Você não tem acesso a este material.', 'danger')
            return redirect(url_for('student.student_dashboard'))
    
    elif current_user.user_type == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Perfil de professor não encontrado.', 'danger')
            return redirect(url_for('main.index'))
        
        # Check if teacher teaches this course
        course = Course.query.get(material.course_id)
        if course and course.teacher_id != teacher.id:
            flash('Você não tem acesso a este material.', 'danger')
            return redirect(url_for('teacher.teacher_dashboard'))
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    return send_from_directory(upload_folder, material.filename, as_attachment=True)

@admin.route('/material/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(material_id):
    if current_user.user_type not in ['admin', 'secretary']:
        return jsonify({'error': 'Acesso negado'}), 403
    
    material = Material.query.get_or_404(material_id)
    
    # Delete file from filesystem
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_folder, material.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    db.session.delete(material)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Material excluído com sucesso'})

@admin.route('/course/<int:course_id>/upload-material', methods=['POST'])
@login_required
def upload_material(course_id):
    if current_user.user_type not in ['admin', 'secretary', 'teacher']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    course = Course.query.get_or_404(course_id)
    
    # Check if teacher is uploading for their own course
    if current_user.user_type == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher or course.teacher_id != teacher.id:
            flash('Você só pode enviar materiais para seus próprios cursos.', 'danger')
            return redirect(url_for('teacher.teacher_dashboard'))
    
    title = request.form.get('title')
    description = request.form.get('description')
    file = request.files.get('file')
    
    if not title or not file:
        flash('Título e arquivo são obrigatórios.', 'danger')
        return redirect(url_for('admin.course_materials', course_id=course_id))
    
    if file.filename and not allowed_file(file.filename):
        flash('Tipo de arquivo não permitido.', 'danger')
        return redirect(url_for('admin.course_materials', course_id=course_id))
    
    # Create upload directory if it doesn't exist
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save file
    filename = secure_filename(file.filename or 'unnamed')
    # Add timestamp to avoid conflicts
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # Get file info
    file_size = os.path.getsize(file_path)
    file_type = ext[1:].lower() if ext else None
    
    # Create material record
    material = Material()
    material.title = title
    material.description = description
    material.filename = filename
    material.file_type = file_type
    material.file_size = file_size
    material.course_id = course_id
    material.uploaded_by_id = current_user.id
    material.uploaded_at = datetime.now()
    
    db.session.add(material)
    db.session.commit()
    
    flash('Material enviado com sucesso!', 'success')
    return redirect(url_for('admin.course_materials', course_id=course_id))

@admin.route('/material/<int:material_id>/preview')
@login_required
def preview_material(material_id):
    if current_user.user_type not in ['admin', 'secretary', 'teacher', 'student']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    material = Material.query.get_or_404(material_id)
    
    # Same access control as download
    if current_user.user_type == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Perfil de estudante não encontrado.', 'danger')
            return redirect(url_for('main.index'))
        
        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            course_id=material.course_id,
            status='active'
        ).first()
        
        if not enrollment:
            flash('Você não tem acesso a este material.', 'danger')
            return redirect(url_for('student.student_dashboard'))
    
    elif current_user.user_type == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        if not teacher:
            flash('Perfil de professor não encontrado.', 'danger')
            return redirect(url_for('main.index'))
        
        course = Course.query.get(material.course_id)
        if course and course.teacher_id != teacher.id:
            flash('Você não tem acesso a este material.', 'danger')
            return redirect(url_for('teacher.teacher_dashboard'))
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    # For preview, serve inline instead of as attachment
    if material.file_type in ['pdf', 'jpg', 'jpeg', 'png', 'gif']:
        return send_from_directory(upload_folder, material.filename)
    else:
        # For other file types, download instead
        return send_from_directory(upload_folder, material.filename, as_attachment=True)
