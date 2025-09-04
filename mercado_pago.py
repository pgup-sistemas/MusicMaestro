import os
import requests
from datetime import datetime
from flask import current_app

class MercadoPagoAPI:
    def __init__(self):
        self.access_token = os.environ.get('MP_ACCESS_TOKEN')
        self.public_key = os.environ.get('MP_PUBLIC_KEY')
        self.base_url = 'https://api.mercadopago.com'

    def create_payment_preference(self, payment_data):
        """
        Cria uma preferência de pagamento no Mercado Pago
        """
        if not self.access_token:
            raise ValueError("Token de acesso do Mercado Pago não configurado")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        # URL base para redirecionamentos
        base_url = self.get_base_url()

        preference_data = {
            "items": [{
                "id": str(payment_data.get('id')),
                "title": payment_data.get('description', 'Pagamento'),
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(payment_data.get('amount', 0))
            }],
            "back_urls": {
                "success": f"{base_url}/payment/success",
                "failure": f"{base_url}/payment/failure",
                "pending": f"{base_url}/payment/pending"
            },
            "auto_return": "approved",
            "external_reference": str(payment_data.get('external_reference')),
            "notification_url": f"{base_url}/mercado_pago/webhook"
        }

        try:
            response = requests.post(
                f'{self.base_url}/checkout/preferences',
                headers=headers,
                json=preference_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao criar preferência de pagamento: {str(e)}")

    def get_payment_info(self, payment_id):
        """
        Obtém informações sobre um pagamento específico
        """
        if not self.access_token:
            raise ValueError("Token de acesso do Mercado Pago não configurado")

        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            response = requests.get(
                f'{self.base_url}/v1/payments/{payment_id}',
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao obter informações do pagamento: {str(e)}")

    def get_base_url(self):
        """
        Obtém a URL base do ambiente (Replit ou produção)
        """
        # Em produção no Replit, usar o domínio do deployment
        if os.environ.get('REPLIT_DEPLOYMENT'):
            return f"https://{os.environ.get('REPLIT_DEPLOYMENT')}"

        # Em desenvolvimento no Replit
        replit_domain = os.environ.get('REPLIT_DEV_DOMAIN')
        if replit_domain:
            return f"https://{replit_domain}"

        # Fallback para localhost
        return "http://localhost:5000"

def process_mercado_pago_webhook(webhook_data):
    """
    Processa o webhook do Mercado Pago
    """
    from models import Payment, db
    from notification_service import NotificationService

    try:
        # Verifica se é uma notificação de pagamento
        if webhook_data.get('type') != 'payment':
            return False

        payment_id = webhook_data.get('data', {}).get('id')
        if not payment_id:
            return False

        # Obter informações do pagamento
        mp_api = MercadoPagoAPI()
        payment_info = mp_api.get_payment_info(payment_id)

        # Encontrar o pagamento no banco de dados
        external_reference = payment_info.get('external_reference')
        if not external_reference:
            return False

        payment = Payment.query.filter_by(id=external_reference).first()
        if not payment:
            return False

        # Atualizar status do pagamento baseado no status do Mercado Pago
        mp_status = payment_info.get('status')
        if mp_status == 'approved':
            payment.status = 'paid'
            payment.payment_date = datetime.utcnow()
            payment.transaction_id = str(payment_id)

            # Enviar notificação de pagamento aprovado
            notification_service = NotificationService()
            notification_service.send_payment_confirmation(payment)

        elif mp_status == 'cancelled':
            payment.status = 'cancelled'
        elif mp_status == 'pending':
            payment.status = 'pending'
        elif mp_status == 'rejected':
            payment.status = 'failed'

        db.session.commit()
        return True

    except Exception as e:
        print(f"Erro ao processar webhook do Mercado Pago: {str(e)}")
        return False

# Instância global da API
mp_api = MercadoPagoAPI()