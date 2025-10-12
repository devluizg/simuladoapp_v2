from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import CreditoUsuario


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def criar_credito_usuario(sender, instance, created, **kwargs):
    """
    Sinal que cria automaticamente um CreditoUsuario quando um novo User é criado.
    Por padrão, novos usuários começam com 5 créditos gratuitos.
    """
    if created:
        CreditoUsuario.objects.create(
            user=instance,
            total_creditos=5,  # Créditos iniciais gratuitos
            usados_creditos=0
        )