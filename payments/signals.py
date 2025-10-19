# payments/signals.py
"""
Signals para o sistema de pagamentos
Automações baseadas em eventos do Django
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Subscription, Payment
import logging

logger = logging.getLogger('payments')


@receiver(post_save, sender=Subscription)
def clear_subscription_cache(sender, instance, **kwargs):
    """
    Limpa o cache quando uma assinatura é atualizada
    """
    cache_key = f'subscription_{instance.user.id}'
    cache.delete(cache_key)
    logger.info(f"Cache limpo para assinatura do usuário {instance.user.username}")


@receiver(post_save, sender=Payment)
def log_payment(sender, instance, created, **kwargs):
    """
    Loga quando um pagamento é criado/atualizado
    """
    if created:
        logger.info(f"Novo pagamento criado: R$ {instance.amount} - {instance.user.username}")
    else:
        logger.info(f"Pagamento atualizado: {instance.id} - Status: {instance.status}")


@receiver(pre_delete, sender=Subscription)
def log_subscription_deletion(sender, instance, **kwargs):
    """
    Loga quando uma assinatura é deletada
    """
    logger.warning(f"Assinatura deletada: {instance.user.username} - Plano: {instance.plan.name}")


# Você pode adicionar mais signals conforme necessário:
# - Enviar email quando assinatura expira
# - Notificar sobre pagamento falho
# - etc.