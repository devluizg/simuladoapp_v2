# payments/context_processors.py
"""
Context processors para adicionar informações de assinatura em todos os templates
"""

from .permissions import get_user_subscription, get_subscription_info

def subscription_context(request):
    """
    Adiciona informações de assinatura ao contexto de todos os templates
    
    Usage no settings.py:
        TEMPLATES = [{
            'OPTIONS': {
                'context_processors': [
                    ...
                    'payments.context_processors.subscription_context',
                ],
            },
        }]
    """
    if not request.user.is_authenticated:
        return {
            'subscription': None,
            'has_subscription': False,
            'subscription_info': None,
        }
    
    subscription = getattr(request, 'subscription', None)
    
    if not subscription:
        subscription = get_user_subscription(request.user)
    
    return {
        'subscription': subscription,
        'has_subscription': subscription is not None,
        'subscription_info': get_subscription_info(request.user),
        'subscription_plan': subscription.plan if subscription else None,
    }


def subscription_features(request):
    """
    Adiciona funções helper para verificar features nos templates
    
    Usage no template:
        {% if has_feature.custom_student_app %}
            <a href="/custom-app/">Meu App</a>
        {% endif %}
    """
    if not request.user.is_authenticated:
        return {'has_feature': {}}
    
    subscription = getattr(request, 'subscription', None)
    
    if not subscription:
        return {'has_feature': {}}
    
    return {
        'has_feature': {
            'personalized_question_bank': subscription.plan.personalized_question_bank,
            'automatic_correction': subscription.plan.automatic_correction,
            'performance_dashboard': subscription.plan.performance_dashboard,
            'custom_student_app': subscription.plan.custom_student_app,
            'advanced_reports': subscription.plan.advanced_reports,
            'priority_support': subscription.plan.priority_support,
        }
    }