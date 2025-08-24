import os
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory
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
            return redirect(url_for('student.dashboard'))
        elif current_user.user_type == 'teacher':
            return redirect(url_for('teacher.dashboard'))
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
        if user and user.is_active and check_password_hash(user.password_hash, form.password.data):
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
            password_hash=generate_password_hash(form.password.data),
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
    
    students = db.session.query(Student, User).join(User).all()
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

@admin.route('/teachers')
@login_required
def teachers():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    teachers = db.session.query(Teacher, User).join(User).all()
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

@admin.route('/courses')
@login_required
def courses():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    courses = db.session.query(Course, Teacher, User).outerjoin(Teacher).outerjoin(User).all()
    return render_template('admin/courses.html', courses=courses)

@admin.route('/course/add', methods=['GET', 'POST'])
@login_required
def add_course():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    form = CourseForm()
    # Populate teacher choices
    teachers = db.session.query(Teacher, User).join(User).all()
    form.teacher_id.choices = [(0, 'Selecione um professor')] + [(t.Teacher.id, t.User.full_name) for t in teachers]
    
    if form.validate_on_submit():
        course = Course(
            name=form.name.data,
            description=form.description.data,
            instrument=form.instrument.data,
            level=form.level.data,
            duration_months=form.duration_months.data,
            monthly_price=form.monthly_price.data,
            max_students=form.max_students.data,
            teacher_id=form.teacher_id.data if form.teacher_id.data != 0 else None,
            is_active=form.is_active.data
        )
        db.session.add(course)
        db.session.commit()
        
        flash('Curso adicionado com sucesso!', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/course_form.html', form=form, title='Adicionar Curso')

@admin.route('/schedule')
@login_required
def schedule():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    schedules = db.session.query(Schedule, Course, Teacher, User, Room).join(Course).join(Teacher).join(User).join(Room).all()
    return render_template('admin/schedule.html', schedules=schedules)

@admin.route('/finances')
@login_required
def finances():
    if current_user.user_type not in ['admin', 'secretary']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.index'))
    
    payments = db.session.query(Payment, Student, User).join(Student).join(User).all()
    return render_template('admin/finances.html', payments=payments)

# Student routes
@student_bp.route('/dashboard')
@login_required
def dashboard():
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
def dashboard():
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
