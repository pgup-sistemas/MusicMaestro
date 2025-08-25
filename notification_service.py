
from datetime import datetime, date, timedelta
from flask import current_app
from models import Payment, Student, User, db
from utils import send_email
import logging

class NotificationService:
    @staticmethod
    def send_payment_reminder(payment_id, reminder_type='warning'):
        """Envia lembrete de pagamento"""
        payment = Payment.query.get(payment_id)
        if not payment:
            return False
            
        student = Student.query.get(payment.student_id)
        user = User.query.get(student.user_id)
        
        if reminder_type == 'warning':
            subject = f'Lembrete: Pagamento vence em 3 dias - Escola Sol Maior'
            template = 'email/payment_warning.html'
        elif reminder_type == 'overdue':
            subject = f'Pagamento em atraso - Escola Sol Maior'
            template = 'email/payment_overdue.html'
        else:
            subject = f'Lembrete de pagamento - Escola Sol Maior'
            template = 'email/payment_reminder.html'
            
        try:
            send_email(
                to=user.email,
                subject=subject,
                template=template,
                payment=payment,
                student=student,
                user=user
            )
            
            # Log da notificação
            logging.info(f'Notificação enviada para {user.email} - Pagamento {payment.id}')
            return True
            
        except Exception as e:
            logging.error(f'Erro ao enviar notificação: {e}')
            return False
    
    @staticmethod
    def check_and_send_payment_reminders():
        """Verifica e envia lembretes automáticos"""
        today = date.today()
        
        # Pagamentos que vencem em 3 dias
        warning_date = today + timedelta(days=3)
        warning_payments = Payment.query.filter(
            Payment.status == 'pending',
            Payment.due_date == warning_date
        ).all()
        
        for payment in warning_payments:
            NotificationService.send_payment_reminder(payment.id, 'warning')
        
        # Pagamentos vencidos
        overdue_payments = Payment.query.filter(
            Payment.status == 'pending',
            Payment.due_date < today
        ).all()
        
        for payment in overdue_payments:
            # Atualizar status para vencido
            payment.status = 'overdue'
            NotificationService.send_payment_reminder(payment.id, 'overdue')
        
        db.session.commit()
        
        return {
            'warning_sent': len(warning_payments),
            'overdue_sent': len(overdue_payments)
        }
    
    @staticmethod
    def send_enrollment_confirmation(enrollment_id):
        """Envia confirmação de matrícula"""
        from models import Enrollment, Course
        
        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            return False
            
        student = Student.query.get(enrollment.student_id)
        user = User.query.get(student.user_id)
        course = Course.query.get(enrollment.course_id)
        
        try:
            send_email(
                to=user.email,
                subject=f'Confirmação de Matrícula - {course.name}',
                template='email/enrollment_confirmation.html',
                enrollment=enrollment,
                student=student,
                user=user,
                course=course
            )
            return True
            
        except Exception as e:
            logging.error(f'Erro ao enviar confirmação de matrícula: {e}')
            return False
