import os
import requests
import json
from datetime import datetime
from flask import current_app

class MercadoPagoAPI:
    def __init__(self):
        self.access_token = os.environ.get('MP_ACCESS_TOKEN')
        self.public_key = os.environ.get('MP_PUBLIC_KEY')
        self.base_url = 'https://api.mercadopago.com'
        
    def create_preference(self, items, payer_info=None, back_urls=None):
        """
        Cria uma preferência de pagamento no Mercado Pago
        """
        if not self.access_token:
            raise ValueError("Token de acesso do Mercado Pago não configurado")
            
        url = f"{self.base_url}/checkout/preferences"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Configuração padrão para URLs de retorno
        if not back_urls:
            base_url = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
            if not base_url.startswith('http'):
                base_url = f"https://{base_url}"
                
            back_urls = {
                "success": f"{base_url}/payment/success",
                "failure": f"{base_url}/payment/failure", 
                "pending": f"{base_url}/payment/pending"
            }
        
        # Dados da preferência
        preference_data = {
            "items": items,
            "back_urls": back_urls,
            "auto_return": "approved",
            "payment_methods": {
                "excluded_payment_types": [],
                "installments": 12,
                "default_installments": 1
            },
            "notification_url": f"{back_urls['success'].replace('/success', '/webhook')}",
            "statement_descriptor": "ESCOLA SOL MAIOR"
        }
        
        # Adicionar informações do pagador se fornecidas
        if payer_info:
            preference_data["payer"] = payer_info
            
        try:
            response = requests.post(url, headers=headers, json=preference_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro ao criar preferência MP: {e}")
            if hasattr(e, 'response') and e.response:
                current_app.logger.error(f"Response: {e.response.text}")
            raise
    
    def get_payment_info(self, payment_id):
        """
        Obtém informações de um pagamento
        """
        if not self.access_token:
            raise ValueError("Token de acesso do Mercado Pago não configurado")
            
        url = f"{self.base_url}/v1/payments/{payment_id}"
        
        headers = {
            'Authorization': f'Bearer {self.access_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Erro ao obter info do pagamento MP: {e}")
            raise
    
    def process_webhook_notification(self, notification_data):
        """
        Processa notificações webhook do Mercado Pago
        """
        if notification_data.get('type') == 'payment':
            payment_id = notification_data.get('data', {}).get('id')
            if payment_id:
                return self.get_payment_info(payment_id)
        return None

# Instância global da API
mp_api = MercadoPagoAPI()