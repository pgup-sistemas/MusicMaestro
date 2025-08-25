
import logging
from datetime import date, timedelta
from app import db
from models import Payment, Student, User
from utils import send_email

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
                subject=subject,
                body=f'''
                Olá {user.full_name},

                {'Seu pagamento vence em 3 dias.' if reminder_type == 'warning' else 'Seu pagamento está em atraso.'}
                
                Valor: R$ {payment.amount:.2f}
                Vencimento: {payment.due_date.strftime('%d/%m/%Y')}
                Referência: {payment.reference_month.strftime('%m/%Y')}
                
                Por favor, regularize sua situação o mais breve possível.
                
                Atenciosamente,
                Escola Sol Maior
                ''',
                recipients=[user.email]
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
                subject=f'Confirmação de Matrícula - Escola Sol Maior',
                body=f'''
                Olá {user.full_name},

                Sua matrícula foi confirmada!
                
                Curso: {course.name}
                Data da Matrícula: {enrollment.enrollment_date.strftime('%d/%m/%Y')}
                Mensalidade: R$ {enrollment.monthly_payment:.2f}
                
                Seja bem-vindo(a) à Escola Sol Maior!
                
                Atenciosamente,
                Equipe Sol Maior
                ''',
                recipients=[user.email]
            )
            
            logging.info(f'Confirmação de matrícula enviada para {user.email}')
            return True
            
        except Exception as e:
            logging.error(f'Erro ao enviar confirmação de matrícula: {e}')
            return False
