
from datetime import datetime
from flask import current_app, request
from flask_login import current_user
import json
import os

class AuditLogger:
    @staticmethod
    def log_action(action, entity_type, entity_id, details=None):
        """
        Registra uma ação no log de auditoria
        
        Args:
            action (str): Tipo de ação (CREATE, UPDATE, DELETE, LOGIN, etc.)
            entity_type (str): Tipo de entidade (User, Student, Payment, etc.)
            entity_id (int): ID da entidade afetada
            details (dict): Detalhes adicionais da ação
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': current_user.id if current_user.is_authenticated else None,
                'user_name': current_user.full_name if current_user.is_authenticated else 'Anonymous',
                'action': action,
                'entity_type': entity_type,
                'entity_id': entity_id,
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.user_agent.string if request else None,
                'details': details or {}
            }
            
            # Criar diretório de logs se não existir
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)
            
            # Nome do arquivo baseado na data
            log_filename = f"audit_{datetime.now().strftime('%Y%m%d')}.log"
            log_path = os.path.join(log_dir, log_filename)
            
            # Escrever no arquivo
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            current_app.logger.error(f'Audit log error: {e}')
    
    @staticmethod
    def log_login(success=True):
        """Log de tentativa de login"""
        AuditLogger.log_action(
            'LOGIN_SUCCESS' if success else 'LOGIN_FAILED',
            'User',
            current_user.id if success and current_user.is_authenticated else None,
            {'success': success}
        )
    
    @staticmethod
    def log_student_action(action, student_id, details=None):
        """Log de ações relacionadas a alunos"""
        AuditLogger.log_action(action, 'Student', student_id, details)
    
    @staticmethod
    def log_payment_action(action, payment_id, details=None):
        """Log de ações relacionadas a pagamentos"""
        AuditLogger.log_action(action, 'Payment', payment_id, details)
    
    @staticmethod
    def log_enrollment_action(action, enrollment_id, details=None):
        """Log de ações relacionadas a matrículas"""
        AuditLogger.log_action(action, 'Enrollment', enrollment_id, details)
    
    @staticmethod
    def get_logs(start_date=None, end_date=None, user_id=None, action=None):
        """
        Recupera logs de auditoria com filtros
        """
        try:
            logs = []
            log_dir = 'logs'
            
            if not os.path.exists(log_dir):
                return logs
            
            # Listar arquivos de log
            log_files = [f for f in os.listdir(log_dir) if f.startswith('audit_') and f.endswith('.log')]
            log_files.sort(reverse=True)  # Mais recentes primeiro
            
            for log_file in log_files:
                log_path = os.path.join(log_dir, log_file)
                
                with open(log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Aplicar filtros
                            if start_date:
                                log_date = datetime.fromisoformat(log_entry['timestamp']).date()
                                if log_date < start_date:
                                    continue
                            
                            if end_date:
                                log_date = datetime.fromisoformat(log_entry['timestamp']).date()
                                if log_date > end_date:
                                    continue
                            
                            if user_id and log_entry.get('user_id') != user_id:
                                continue
                            
                            if action and log_entry.get('action') != action:
                                continue
                            
                            logs.append(log_entry)
                            
                        except json.JSONDecodeError:
                            continue
            
            return logs[:1000]  # Limitar a 1000 registros
            
        except Exception as e:
            current_app.logger.error(f'Error reading audit logs: {e}')
            return []
