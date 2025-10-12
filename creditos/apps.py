from django.apps import AppConfig


class CreditosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'creditos'
    verbose_name = 'Sistema de Créditos'

    def ready(self):
        """Importa os signals quando o app está pronto"""
        import creditos.signals