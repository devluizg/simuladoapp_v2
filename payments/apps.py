# payments/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaymentsConfig(AppConfig):
    """Configuração do app de pagamentos"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = _('Sistema de Pagamentos')
    
    def ready(self):
        """
        Código executado quando o app é carregado
        """
        # Importa os signals
        try:
            import payments.signals  # noqa: F401
        except ImportError as e:
            import warnings
            warnings.warn(f"Não foi possível importar signals: {e}", UserWarning)
        
        # Verifica configurações do Stripe
        self.check_stripe_configuration()
    
    def check_stripe_configuration(self):
        """
        Verifica se as configurações do Stripe estão corretas
        """
        from django.conf import settings
        import warnings
        
        required_settings = [
            'STRIPE_PUBLIC_KEY',
            'STRIPE_SECRET_KEY',
            'STRIPE_WEBHOOK_SECRET',
        ]
        
        missing_settings = []
        
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            warnings.warn(
                f"As seguintes configurações do Stripe estão faltando: {', '.join(missing_settings)}. "
                f"O sistema de pagamentos pode não funcionar corretamente.",
                UserWarning
            )
        
        # Verifica se as chaves parecem válidas
        if hasattr(settings, 'STRIPE_PUBLIC_KEY'):
            public_key = settings.STRIPE_PUBLIC_KEY
            if public_key and not public_key.startswith('pk_'):
                warnings.warn(
                    "STRIPE_PUBLIC_KEY não parece ser uma chave pública válida (deve começar com 'pk_')",
                    UserWarning
                )
        
        if hasattr(settings, 'STRIPE_SECRET_KEY'):
            secret_key = settings.STRIPE_SECRET_KEY
            if secret_key and not secret_key.startswith('sk_'):
                warnings.warn(
                    "STRIPE_SECRET_KEY não parece ser uma chave secreta válida (deve começar com 'sk_')",
                    UserWarning
                )
        
        if hasattr(settings, 'STRIPE_WEBHOOK_SECRET'):
            webhook_secret = settings.STRIPE_WEBHOOK_SECRET
            if webhook_secret and not webhook_secret.startswith('whsec_'):
                warnings.warn(
                    "STRIPE_WEBHOOK_SECRET não parece ser um webhook secret válido (deve começar com 'whsec_')",
                    UserWarning
                )