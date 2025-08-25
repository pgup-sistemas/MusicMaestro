
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from functools import wraps
import jwt
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from models import *
from app import db
from sqlalchemy import and_

api = Blueprint('api', __name__, url_prefix='/api/v1')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token é obrigatório'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({'error': 'Token inválido'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

@api.route('/auth/token', methods=['POST'])
def get_token():
    """Gerar token de acesso para API"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.is_active and check_password_hash(user.password_hash, data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'expires_in': 86400,  # 24 horas
            'user': {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'type': user.user_type
            }
        })
    
    return jsonify({'error': 'Credenciais inválidas'}), 401

@api.route('/students', methods=['GET'])
@token_required
def api_students():
    """Listar alunos"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    students = db.session.query(Student, User).join(User).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'students': [{
            'id': student.id,
            'name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'birth_date': student.birth_date.isoformat() if student.birth_date else None,
            'registration_date': student.registration_date.isoformat() if student.registration_date else None,
            'is_active': user.is_active
        } for student, user in students.items],
        'pagination': {
            'page': students.page,
            'pages': students.pages,
            'per_page': students.per_page,
            'total': students.total
        }
    })

@api.route('/students/<int:student_id>', methods=['GET'])
@token_required
def api_student_detail(student_id):
    """Detalhes de um aluno"""
    student = Student.query.get_or_404(student_id)
    user = User.query.get_or_404(student.user_id)
    
    # Buscar matrículas
    enrollments = db.session.query(Enrollment, Course).join(Course).filter(
        Enrollment.student_id == student_id
    ).all()
    
    # Buscar pagamentos
    payments = Payment.query.filter_by(student_id=student_id).order_by(
        Payment.due_date.desc()
    ).limit(10).all()
    
    return jsonify({
        'id': student.id,
        'name': user.full_name,
        'email': user.email,
        'phone': user.phone,
        'birth_date': student.birth_date.isoformat() if student.birth_date else None,
        'address': student.address,
        'emergency_contact': student.emergency_contact,
        'emergency_phone': student.emergency_phone,
        'registration_date': student.registration_date.isoformat() if student.registration_date else None,
        'is_active': user.is_active,
        'enrollments': [{
            'id': enrollment.id,
            'course_name': course.name,
            'course_instrument': course.instrument,
            'enrollment_date': enrollment.enrollment_date.isoformat(),
            'status': enrollment.status,
            'monthly_payment': float(enrollment.monthly_payment or course.monthly_price)
        } for enrollment, course in enrollments],
        'recent_payments': [{
            'id': payment.id,
            'amount': float(payment.amount),
            'due_date': payment.due_date.isoformat(),
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'status': payment.status,
            'reference_month': payment.reference_month.isoformat()
        } for payment in payments]
    })

@api.route('/payments', methods=['GET'])
@token_required
def api_payments():
    """Listar pagamentos"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    status = request.args.get('status')
    
    query = db.session.query(Payment, Student, User).join(
        Student, Payment.student_id == Student.id
    ).join(User, Student.user_id == User.id)
    
    if status:
        query = query.filter(Payment.status == status)
    
    payments = query.order_by(Payment.due_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payments': [{
            'id': payment.id,
            'student_name': user.full_name,
            'student_email': user.email,
            'amount': float(payment.amount),
            'due_date': payment.due_date.isoformat(),
            'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
            'status': payment.status,
            'payment_method': payment.payment_method,
            'reference_month': payment.reference_month.isoformat()
        } for payment, student, user in payments.items],
        'pagination': {
            'page': payments.page,
            'pages': payments.pages,
            'per_page': payments.per_page,
            'total': payments.total
        }
    })

@api.route('/courses', methods=['GET'])
@token_required
def api_courses():
    """Listar cursos"""
    courses = Course.query.filter_by(is_active=True).all()
    
    return jsonify({
        'courses': [{
            'id': course.id,
            'name': course.name,
            'description': course.description,
            'instrument': course.instrument,
            'level': course.level,
            'monthly_price': float(course.monthly_price),
            'max_students': course.max_students,
            'teacher_id': course.teacher_id
        } for course in courses]
    })

@api.route('/stats', methods=['GET'])
@token_required
def api_stats():
    """Estatísticas gerais"""
    total_students = Student.query.count()
    active_students = db.session.query(Student).join(User).filter(User.is_active == True).count()
    total_courses = Course.query.filter_by(is_active=True).count()
    pending_payments = Payment.query.filter_by(status='pending').count()
    
    # Receita do mês atual
    from sqlalchemy import func, extract
    current_month_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.status == 'paid',
        extract('month', Payment.payment_date) == datetime.now().month,
        extract('year', Payment.payment_date) == datetime.now().year
    ).scalar() or 0
    
    return jsonify({
        'total_students': total_students,
        'active_students': active_students,
        'total_courses': total_courses,
        'pending_payments': pending_payments,
        'current_month_revenue': float(current_month_revenue)
    })

@api.route('/experimental-classes', methods=['POST'])
def api_create_experimental_class():
    """Criar solicitação de aula experimental via API"""
    data = request.get_json()
    
    required_fields = ['name', 'email', 'phone', 'instrument']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Campo {field} é obrigatório'}), 400
    
    experimental_class = ExperimentalClass(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        instrument=data['instrument'],
        experience_level=data.get('experience_level', 'none'),
        preferred_date=datetime.strptime(data['preferred_date'], '%Y-%m-%d').date() if data.get('preferred_date') else None,
        preferred_time=data.get('preferred_time'),
        notes=data.get('notes')
    )
    
    db.session.add(experimental_class)
    db.session.commit()
    
    return jsonify({
        'id': experimental_class.id,
        'message': 'Solicitação de aula experimental criada com sucesso'
    }), 201
