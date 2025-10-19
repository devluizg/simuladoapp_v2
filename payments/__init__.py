# payments/__init__.py
"""
App de pagamentos e assinaturas com Stripe
"""

default_app_config = 'payments.apps.PaymentsConfig'

__version__ = '1.0.0'
__author__ = 'Seu Nome'

# NÃO FAÇA IMPORTS AQUI!
# Deixe vazio ou apenas metadados

# Os imports devem ser feitos diretamente onde você usar:
# from payments.permissions import subscription_required
# from payments.services import StripeService