# payments/permissions.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import Subscription


def get_user_subscription(user):
    """
    Retorna a assinatura ativa do usuário
    
    Args:
        user: Objeto User do Django
        
    Returns:
        Subscription object ou None
    """
    if not user.is_authenticated:
        return None
    
    try:
        subscription = Subscription.objects.filter(
            user=user,
            status__in=['active', 'trialing']
        ).select_related('plan').latest('created_at')
        
        if subscription.is_valid:
            return subscription
    except Subscription.DoesNotExist:
        pass
    
    return None


def subscription_required(redirect_url=None, message=None, raise_exception=False):
    """
    Decorator que exige assinatura ativa
    
    Args:
        redirect_url: URL para redirecionar se não tiver assinatura
        message: Mensagem customizada
        raise_exception: Se True, levanta PermissionDenied ao invés de redirecionar
    
    Uso:
        @subscription_required()
        @subscription_required(redirect_url='/custom-page/')
        @subscription_required(raise_exception=True)
    """
    redirect_url = redirect_url or '/payments/plans/'
    message = message or 'Você precisa de uma assinatura ativa para acessar esta funcionalidade.'
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado.')
                return redirect('/login/')
            
            subscription = get_user_subscription(request.user)
            
            if not subscription:
                if raise_exception:
                    raise PermissionDenied(message)
                messages.warning(request, message)
                return redirect(redirect_url)
            
            # Adiciona a assinatura no request para uso posterior
            request.subscription = subscription
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def feature_required(feature_name, redirect_url=None, message=None, raise_exception=False):
    """
    Decorator que exige uma feature específica no plano
    
    Args:
        feature_name: Nome do campo booleano no modelo Plan
        redirect_url: URL para redirecionar
        message: Mensagem customizada
        raise_exception: Se True, levanta PermissionDenied
    
    Uso:
        @feature_required('custom_student_app')
        @feature_required('advanced_reports', message='Faça upgrade para ter relatórios avançados')
    """
    redirect_url = redirect_url or '/payments/plans/'
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado.')
                return redirect('/login/')
            
            subscription = get_user_subscription(request.user)
            
            if not subscription:
                msg = 'Você precisa de uma assinatura ativa.'
                if raise_exception:
                    raise PermissionDenied(msg)
                messages.warning(request, msg)
                return redirect('/payments/plans/')
            
            if not subscription.has_feature(feature_name):
                msg = message or f'Esta funcionalidade não está disponível no seu plano atual. Faça upgrade!'
                if raise_exception:
                    raise PermissionDenied(msg)
                messages.warning(request, msg)
                return redirect(redirect_url)
            
            request.subscription = subscription
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def class_limit_check(redirect_url=None, message=None):
    """
    Decorator para verificar limite de turmas
    
    Args:
        redirect_url: URL para redirecionar
        message: Mensagem customizada
    
    Uso:
        @class_limit_check()
        @class_limit_check(message='Limite de turmas atingido! Adicione turmas extras.')
    """
    redirect_url = redirect_url or '/payments/subscription/'
    message = message or 'Você atingiu o limite de turmas do seu plano.'
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado.')
                return redirect('/login/')
            
            subscription = get_user_subscription(request.user)
            
            if not subscription:
                messages.warning(request, 'Você precisa de uma assinatura ativa.')
                return redirect('/payments/plans/')
            
            # Tenta importar o modelo de turmas do projeto
            current_classes = 0
            try:
                # ===== CORRIGIDO: Tenta importar de classes.models =====
                from classes.models import Class
                current_classes = Class.objects.filter(teacher=request.user).count()
            except (ImportError, AttributeError):
                # Se não existir o modelo, permite passar
                pass
            except Exception as e:
                # Qualquer outro erro, loga mas permite passar
                import logging
                logger = logging.getLogger('payments')
                logger.warning(f"Erro ao verificar limite de turmas: {e}")
            
            if not subscription.can_create_class(current_classes):
                messages.warning(request, message)
                return redirect(redirect_url)
            
            request.subscription = subscription
            request.current_classes_count = current_classes
            remaining = subscription.total_classes_allowed - current_classes
            request.remaining_classes = remaining if remaining != float('inf') else -1
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def test_version_limit_check(redirect_url=None, message=None):
    """
    Decorator para verificar limite de versões de teste/simulado
    
    Uso:
        @test_version_limit_check()
    """
    redirect_url = redirect_url or '/payments/subscription/'
    message = message or 'Você atingiu o limite de versões de simulado do seu plano.'
    
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado.')
                return redirect('/login/')
            
            subscription = get_user_subscription(request.user)
            
            if not subscription:
                messages.warning(request, 'Você precisa de uma assinatura ativa.')
                return redirect('/payments/plans/')
            
            # Pega o número de versões do teste atual
            test_id = kwargs.get('test_id') or request.GET.get('test_id')
            
            if test_id:
                try:
                    # ===== CORRIGIDO: Ajuste conforme seu modelo =====
                    from questions.models import TestVersion
                    current_versions = TestVersion.objects.filter(test_id=test_id).count()
                    
                    if current_versions >= subscription.plan.max_test_versions:
                        messages.warning(request, message)
                        return redirect(redirect_url)
                except (ImportError, AttributeError):
                    # Se não existir o modelo, permite passar
                    pass
                except Exception as e:
                    # Qualquer outro erro, loga mas permite passar
                    import logging
                    logger = logging.getLogger('payments')
                    logger.warning(f"Erro ao verificar limite de versões: {e}")
            
            request.subscription = subscription
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ========== DECORATORS PARA APIs/AJAX ==========

def api_subscription_required(view_func):
    """
    Decorator para APIs que retorna JSON
    
    Uso:
        @api_subscription_required
        def my_api_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Autenticação necessária',
                'code': 'authentication_required'
            }, status=401)
        
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            return JsonResponse({
                'error': 'Assinatura ativa necessária',
                'code': 'subscription_required',
                'redirect': '/payments/plans/'
            }, status=403)
        
        request.subscription = subscription
        return view_func(request, *args, **kwargs)
    
    return wrapper


def api_feature_required(feature_name):
    """
    Decorator para APIs que exige feature específica
    
    Uso:
        @api_feature_required('advanced_reports')
        def my_api_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticação necessária',
                    'code': 'authentication_required'
                }, status=401)
            
            subscription = get_user_subscription(request.user)
            
            if not subscription:
                return JsonResponse({
                    'error': 'Assinatura ativa necessária',
                    'code': 'subscription_required',
                    'redirect': '/payments/plans/'
                }, status=403)
            
            if not subscription.has_feature(feature_name):
                return JsonResponse({
                    'error': f'Feature "{feature_name}" não disponível no seu plano',
                    'code': 'feature_not_available',
                    'feature': feature_name,
                    'redirect': '/payments/subscription/'
                }, status=403)
            
            request.subscription = subscription
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# ========== FUNÇÕES AUXILIARES ==========

def user_can_create_class(user):
    """
    Verifica se o usuário pode criar mais turmas
    
    Returns:
        tuple: (can_create: bool, remaining: int, subscription: Subscription)
    """
    subscription = get_user_subscription(user)
    
    if not subscription:
        return False, 0, None
    
    current_classes = 0
    try:
        # ===== CORRIGIDO: Importa de classes.models =====
        from classes.models import Class
        current_classes = Class.objects.filter(teacher=user).count()
    except (ImportError, AttributeError):
        # Se não existir, retorna 0
        pass
    except Exception as e:
        import logging
        logger = logging.getLogger('payments')
        logger.warning(f"Erro ao contar turmas: {e}")
    
    can_create = subscription.can_create_class(current_classes)
    remaining = subscription.total_classes_allowed - current_classes
    
    if remaining == float('inf'):
        remaining = -1  # -1 significa ilimitado
    
    return can_create, int(remaining) if remaining >= 0 else -1, subscription


def user_has_feature(user, feature_name):
    """
    Verifica se o usuário tem acesso a uma feature
    
    Args:
        user: User object
        feature_name: Nome da feature (ex: 'custom_student_app')
        
    Returns:
        bool
    """
    subscription = get_user_subscription(user)
    
    if not subscription:
        return False
    
    return subscription.has_feature(feature_name)


def get_subscription_info(user):
    """
    Retorna informações completas da assinatura do usuário
    
    Returns:
        dict com informações ou None
    """
    subscription = get_user_subscription(user)
    
    if not subscription:
        return None
    
    return {
        'has_subscription': True,
        'is_active': subscription.is_active,
        'is_valid': subscription.is_valid,
        'plan_name': subscription.plan.name,
        'plan_type': subscription.plan.plan_type,
        'plan_price': float(subscription.plan.price),
        'billing_period': subscription.plan.billing_period,
        'status': subscription.status,
        'current_period_end': subscription.current_period_end,
        'days_until_renewal': subscription.days_until_renewal,
        'cancel_at_period_end': subscription.cancel_at_period_end,
        'max_classes': subscription.total_classes_allowed,
        'extra_classes': subscription.extra_classes,
        'features': {
            'personalized_question_bank': subscription.plan.personalized_question_bank,
            'max_test_versions': subscription.plan.max_test_versions,
            'automatic_correction': subscription.plan.automatic_correction,
            'performance_dashboard': subscription.plan.performance_dashboard,
            'custom_student_app': subscription.plan.custom_student_app,
            'advanced_reports': subscription.plan.advanced_reports,
            'priority_support': subscription.plan.priority_support,
        }
    }


def check_and_warn_limits(request):
    """
    Verifica limites e adiciona avisos se necessário
    Útil para usar em views que precisam alertar o usuário
    
    Usage:
        def my_view(request):
            check_and_warn_limits(request)
            ...
    """
    if not request.user.is_authenticated:
        return
    
    subscription = get_user_subscription(request.user)
    
    if not subscription:
        return
    
    # Verifica limite de turmas
    try:
        # ===== CORRIGIDO: Importa de classes.models =====
        from classes.models import Class
        current_classes = Class.objects.filter(teacher=request.user).count()
        max_classes = subscription.total_classes_allowed
        
        if max_classes != float('inf'):
            remaining = max_classes - current_classes
            
            if remaining <= 0:
                messages.warning(
                    request,
                    f'⚠️ Você atingiu o limite de {int(max_classes)} turmas. '
                    f'<a href="/payments/subscription/">Adicione turmas extras</a> para criar mais.',
                    extra_tags='safe'
                )
            elif remaining <= 2:
                messages.info(
                    request,
                    f'ℹ️ Você tem apenas {int(remaining)} turma(s) restante(s) no seu plano.',
                    extra_tags='safe'
                )
    except (ImportError, AttributeError):
        # Modelo não existe ainda
        pass
    except Exception as e:
        import logging
        logger = logging.getLogger('payments')
        logger.warning(f"Erro ao verificar limites: {e}")
    
    # Verifica se a assinatura vai expirar em breve
    if subscription.days_until_renewal and subscription.days_until_renewal <= 7:
        if subscription.cancel_at_period_end:
            messages.warning(
                request,
                f'⚠️ Sua assinatura será cancelada em {subscription.days_until_renewal} dia(s). '
                f'<a href="/payments/subscription/">Reativar assinatura</a>',
                extra_tags='safe'
            )
        else:
            messages.info(
                request,
                f'ℹ️ Sua assinatura será renovada em {subscription.days_until_renewal} dia(s).'
            )