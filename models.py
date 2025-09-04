from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # admin, secretary, teacher, student
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    _is_active = db.Column('is_active', db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
    
    @property
    def is_active(self):
        return self._is_active
    
    @is_active.setter
    def is_active(self, value):
        self._is_active = value
    
    # Relationships
    student_profile = db.relationship('Student', backref='user', uselist=False, cascade='all, delete-orphan')
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, cascade='all, delete-orphan')

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    birth_date = db.Column(db.Date)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    guardian_name = db.Column(db.String(200))  # For minors
    guardian_phone = db.Column(db.String(20))
    guardian_email = db.Column(db.String(120))
    medical_info = db.Column(db.Text)
    notes = db.Column(db.Text)
    registration_date = db.Column(db.Date, default=date.today)
    
    def __init__(self, **kwargs):
        super(Student, self).__init__(**kwargs)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='student', cascade='all, delete-orphan')
    experimental_classes = db.relationship('ExperimentalClass', backref='student', cascade='all, delete-orphan')

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(200))
    hourly_rate = db.Column(db.Numeric(10, 2))
    bank_name = db.Column(db.String(100))
    bank_agency = db.Column(db.String(20))
    bank_account = db.Column(db.String(20))
    pix_key = db.Column(db.String(100))
    bio = db.Column(db.Text)
    qualifications = db.Column(db.Text)
    hire_date = db.Column(db.Date, default=date.today)
    
    def __init__(self, **kwargs):
        super(Teacher, self).__init__(**kwargs)
    
    # Relationships
    courses = db.relationship('Course', backref='teacher')
    schedules = db.relationship('Schedule', backref='teacher')

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, default=1)
    equipment = db.Column(db.Text)  # JSON string or comma-separated list
    location = db.Column(db.String(200))
    is_available = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super(Room, self).__init__(**kwargs)
    
    # Relationships
    schedules = db.relationship('Schedule', backref='room')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    instrument = db.Column(db.String(100))
    level = db.Column(db.String(50))  # beginner, intermediate, advanced
    duration_months = db.Column(db.Integer)
    monthly_price = db.Column(db.Numeric(10, 2))
    max_students = db.Column(db.Integer, default=1)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, **kwargs):
        super(Course, self).__init__(**kwargs)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', cascade='all, delete-orphan')
    materials = db.relationship('Material', backref='course', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='course')

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrollment_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    discount_percentage = db.Column(db.Numeric(5, 2), default=0)
    monthly_payment = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    payment_method = db.Column(db.String(50))
    reference_month = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Material(db.Model):
    __tablename__ = 'materials'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(500))  # Nome do arquivo
    file_type = db.Column(db.String(50))  # pdf, mp3, mp4, etc.
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    uploaded_by = db.relationship('User', foreign_keys=[uploaded_by_id], backref='uploaded_materials')

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # PIX, CREDIT_CARD, BOLETO
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, expired
    gateway_data = db.Column(db.Text)  # JSON com dados do gateway
    pix_code = db.Column(db.Text)  # Código PIX se aplicável
    pix_qr_code = db.Column(db.Text)  # QR Code PIX se aplicável
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relacionamento
    payment = db.relationship('Payment', backref='transactions')

class News(db.Model):
    __tablename__ = 'news'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text)
    category = db.Column(db.String(50), default='announcement')  # event, announcement, news
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    is_public = db.Column(db.Boolean, default=True)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    views_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(News, self).__init__(**kwargs)
    
    # Relationship to author
    author = db.relationship('User', backref='news_articles')

class ExperimentalClass(db.Model):
    __tablename__ = 'experimental_classes'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    instrument = db.Column(db.String(100), nullable=False)
    experience_level = db.Column(db.String(50))
    preferred_date = db.Column(db.Date)
    preferred_time = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, scheduled, completed, cancelled
    scheduled_date = db.Column(db.DateTime)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(ExperimentalClass, self).__init__(**kwargs)
