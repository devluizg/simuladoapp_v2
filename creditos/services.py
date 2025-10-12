import json
import logging
from typing import Dict, Tuple, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings

logger = logging.getLogger(__name__)

class GooglePlayValidationService:
    """Serviço para validar compras com a API do Google Play"""

    def __init__(self):
        self.package_name = getattr(settings, 'GOOGLE_PLAY_PACKAGE_NAME', '')
        self.service_account_file = getattr(settings, 'GOOGLE_PLAY_SERVICE_ACCOUNT_FILE', '')
        self.scopes = ['https://www.googleapis.com/auth/androidpublisher']

    def _get_service(self):
        """Cria o serviço da API do Google Play"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=self.scopes
            )
            service = build('androidpublisher', 'v3', credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Erro ao criar serviço Google Play: {e}")
            return None

    def validate_purchase(self, product_id: str, purchase_token: str) -> Tuple[bool, Dict]:
        """
        Valida uma compra de produto in-app com o Google Play

        Returns:
            Tuple[bool, Dict]: (is_valid, purchase_data)
        """
        try:
            service = self._get_service()
            if not service:
                return False, {"error": "Erro ao conectar com Google Play API"}

            # Verificar compra de produto in-app
            result = service.purchases().products().get(
                packageName=self.package_name,
                productId=product_id,
                token=purchase_token
            ).execute()

            # Verificar se a compra é válida
            purchase_state = result.get('purchaseState', -1)
            consumption_state = result.get('consumptionState', -1)

            # purchaseState: 0 = Purchased, 1 = Canceled
            # consumptionState: 0 = Yet to be consumed, 1 = Consumed
            is_valid = (
                purchase_state == 0 and  # Compra confirmada
                consumption_state == 0   # Ainda não consumida
            )

            return is_valid, result

        except HttpError as e:
            logger.error(f"Erro HTTP na validação Google Play: {e}")
            if e.resp.status == 410:
                return False, {"error": "Token de compra inválido ou expirado"}
            return False, {"error": f"Erro na API do Google Play: {e}"}

        except Exception as e:
            logger.error(f"Erro inesperado na validação: {e}")
            return False, {"error": "Erro interno na validação"}

    def acknowledge_purchase(self, product_id: str, purchase_token: str) -> bool:
        """
        Reconhece/consome a compra no Google Play
        """
        try:
            service = self._get_service()
            if not service:
                return False

            service.purchases().products().acknowledge(
                packageName=self.package_name,
                productId=product_id,
                token=purchase_token
            ).execute()

            return True

        except Exception as e:
            logger.error(f"Erro ao reconhecer compra: {e}")
            return False