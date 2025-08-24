import os
from flask import current_app
from flask_mail import Message
from app import mail

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'mp4', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(subject, body, recipients):
    """Send email notification"""
    try:
        msg = Message(
            subject=subject,
            body=body,
            recipients=recipients
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Error sending email: {e}')
        return False

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def format_currency(amount):
    """Format currency value"""
    return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_phone(phone):
    """Format phone number"""
    if not phone:
        return ''
    
    # Remove non-numeric characters
    phone = ''.join(filter(str.isdigit, phone))
    
    if len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    elif len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    else:
        return phone

# Template filters
def register_template_filters(app):
    @app.template_filter('currency')
    def currency_filter(amount):
        return format_currency(amount) if amount else 'R$ 0,00'
    
    @app.template_filter('phone')
    def phone_filter(phone):
        return format_phone(phone)
    
    @app.template_filter('date_br')
    def date_br_filter(date):
        if date:
            return date.strftime('%d/%m/%Y')
        return ''
    
    @app.template_filter('datetime_br')
    def datetime_br_filter(datetime):
        if datetime:
            return datetime.strftime('%d/%m/%Y %H:%M')
        return ''
