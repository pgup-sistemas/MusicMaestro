
import requests
import json
import uuid
from datetime import datetime, timedelta
from flask import current_app
import logging

class PaymentGateway:
    """
    Classe para integração com gateway de pagamento
    Adaptável para diferentes provedores (PagSeguro, Mercado Pago, etc.)
    """
    
    def __init__(self):
        self.api_key = current_app.config.get('PAYMENT_API_KEY')
        self.api_url = current_app.config.get('PAYMENT_API_URL')
        self.webhook_url = current_app.config.get('PAYMENT_WEBHOOK_URL')
    
    def create_pix_payment(self, payment_id, amount, description, payer_info):
        """
        Cria um pagamento PIX
        """
        try:
            payload = {
                "transaction_id": f"PAY_{payment_id}_{uuid.uuid4().hex[:8]}",
                "amount": float(amount),
                "description": description,
                "payer": {
                    "name": payer_info.get('name'),
                    "email": payer_info.get('email'),
                    "document": payer_info.get('document', '')
                },
                "payment_method": "PIX",
                "expires_in": 3600,  # 1 hora para expirar
                "webhook_url": f"{self.webhook_url}/payment-webhook"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/payments",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "transaction_id": data.get("id"),
                    "pix_code": data.get("pix_code"),
                    "pix_qr_code": data.get("qr_code"),
                    "expires_at": data.get("expires_at")
                }
            else:
                logging.error(f"Payment Gateway Error: {response.text}")
                return {"success": False, "error": "Erro ao criar pagamento PIX"}
                
        except Exception as e:
            logging.error(f"Payment Gateway Exception: {e}")
            return {"success": False, "error": "Erro de conexão com gateway"}
    
    def create_credit_card_payment(self, payment_id, amount, description, card_info, payer_info):
        """
        Cria um pagamento com cartão de crédito
        """
        try:
            payload = {
                "transaction_id": f"PAY_{payment_id}_{uuid.uuid4().hex[:8]}",
                "amount": float(amount),
                "description": description,
                "payment_method": "CREDIT_CARD",
                "card": {
                    "number": card_info.get('number'),
                    "holder_name": card_info.get('holder_name'),
                    "expiry_month": card_info.get('expiry_month'),
                    "expiry_year": card_info.get('expiry_year'),
                    "cvv": card_info.get('cvv')
                },
                "payer": {
                    "name": payer_info.get('name'),
                    "email": payer_info.get('email'),
                    "document": payer_info.get('document')
                },
                "installments": card_info.get('installments', 1),
                "webhook_url": f"{self.webhook_url}/payment-webhook"
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.api_url}/payments",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "transaction_id": data.get("id"),
                    "status": data.get("status")
                }
            else:
                return {"success": False, "error": "Erro ao processar cartão"}
                
        except Exception as e:
            logging.error(f"Credit Card Payment Exception: {e}")
            return {"success": False, "error": "Erro de conexão"}
    
    def check_payment_status(self, transaction_id):
        """
        Verifica o status de um pagamento
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/payments/{transaction_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data.get("status"),
                    "paid_at": data.get("paid_at"),
                    "amount": data.get("amount")
                }
            else:
                return {"success": False, "error": "Pagamento não encontrado"}
                
        except Exception as e:
            logging.error(f"Payment Status Check Exception: {e}")
            return {"success": False, "error": "Erro de conexão"}

class PaymentProcessor:
    """
    Processador de pagamentos para a escola
    """
    
    @staticmethod
    def process_payment_confirmation(transaction_id, status, paid_amount=None):
        """
        Processa confirmação de pagamento via webhook
        """
        from models import Payment, PaymentTransaction
        
        try:
            # Buscar transação
            transaction = PaymentTransaction.query.filter_by(
                transaction_id=transaction_id
            ).first()
            
            if not transaction:
                logging.error(f"Transaction not found: {transaction_id}")
                return False
            
            # Buscar pagamento
            payment = Payment.query.get(transaction.payment_id)
            if not payment:
                logging.error(f"Payment not found: {transaction.payment_id}")
                return False
            
            # Atualizar status baseado no retorno do gateway
            if status in ['paid', 'approved']:
                payment.status = 'paid'
                payment.payment_date = datetime.now().date()
                payment.payment_method = transaction.payment_method
                transaction.status = 'completed'
                
                # Enviar confirmação por email
                from notification_service import NotificationService
                NotificationService.send_payment_confirmation(payment.id)
                
            elif status in ['cancelled', 'failed']:
                transaction.status = 'failed'
                
            elif status == 'pending':
                transaction.status = 'pending'
            
            db.session.commit()
            logging.info(f"Payment {payment.id} updated to {payment.status}")
            return True
            
        except Exception as e:
            logging.error(f"Payment confirmation error: {e}")
            db.session.rollback()
            return False
