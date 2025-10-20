# payments/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from .permissions import get_user_subscription
import logging

logger = logging.getLogger('payments')


class SubscriptionMiddleware(MiddlewareMixin):
    """
    Middleware que adiciona informações de assinatura em todas as requisições
    e verifica automaticamente limites e avisos
    """
    
    def process_request(self, request):
        """
        Adiciona informações de assinatura ao request
        """
        if request.user.is_authenticated:
            # Usa cache para evitar múltiplas queries
            cache_key = f'subscription_{request.user.id}'
            subscription = cache.get(cache_key)
            
            if subscription is None:
                subscription = get_user_subscription(request.user)
                # Cache por 5 minutos
                cache.set(cache_key, subscription, 300)
            
            request.subscription = subscription
            request.has_active_subscription = subscription is not None
            
            # Adiciona informações úteis
            if subscription:
                request.subscription_plan = subscription.plan
                request.subscription_status = subscription.status
                request.subscription_is_valid = subscription.is_valid
            else:
                request.subscription_plan = None
                request.subscription_status = None
                request.subscription_is_valid = False
        else:
            request.subscription = None
            request.has_active_subscription = False
            request.subscription_plan = None
            request.subscription_status = None
            request.subscription_is_valid = False
        
        return None
    
    def process_template_response(self, request, response):
        """
        Adiciona informações ao contexto do template
        """
        if hasattr(response, 'context_data') and response.context_data is not None:
            response.context_data['subscription'] = getattr(request, 'subscription', None)
            response.context_data['has_active_subscription'] = getattr(request, 'has_active_subscription', False)
        
        return response


class SubscriptionWarningMiddleware(MiddlewareMixin):
    """
    Middleware que adiciona avisos automáticos sobre limites e status da assinatura
    Só mostra avisos 1x por sessão para não incomodar o usuário
    """
    
    def process_request(self, request):
        """
        Verifica e adiciona avisos sobre assinatura
        """
        if not request.user.is_authenticated:
            return None
        
        subscription = getattr(request, 'subscription', None)
        
        if not subscription:
            # Avisa apenas em páginas específicas (não em todas)
            if self._should_warn_no_subscription(request):
                if not request.session.get('warned_no_subscription'):
                    messages.warning(
                        request,
                        '⚠️ Você não possui uma assinatura ativa. '
                        '<a href="/payments/plans/" class="alert-link">Ver planos disponíveis</a>',
                        extra_tags='safe'
                    )
                    request.session['warned_no_subscription'] = True
            return None
        
        # Limpa flag de aviso de não ter assinatura
        if 'warned_no_subscription' in request.session:
            del request.session['warned_no_subscription']
        
        # Verifica se vai expirar em breve
        self._check_expiration_warning(request, subscription)
        
        # Verifica limites de turmas
        self._check_class_limit_warning(request, subscription)
        
        # Verifica status de pagamento
        self._check_payment_status(request, subscription)
        
        return None
    
    def _should_warn_no_subscription(self, request):
        """
        Verifica se deve avisar sobre falta de assinatura nesta página
        """
        # Não avisa em páginas de pagamento
        if request.path.startswith('/payments/'):
            return False
        
        # Não avisa em APIs
        if request.path.startswith('/api/'):
            return False
        
        # Não avisa em admin
        if request.path.startswith('/admin/'):
            return False
        
        # Não avisa em páginas estáticas
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return False
        
        return True
    
    def _check_expiration_warning(self, request, subscription):
        """
        Avisa sobre expiração próxima
        """
        if not subscription.days_until_renewal:
            return
        
        days = subscription.days_until_renewal
        session_key = f'warned_expiration_{days}'
        
        if subscription.cancel_at_period_end:
            # Assinatura será cancelada
            if days <= 7 and not request.session.get(session_key):
                messages.warning(
                    request,
                    f'⚠️ Sua assinatura será <strong>cancelada</strong> em {days} dia(s). '
                    f'<a href="/payments/subscription/" class="alert-link">Reativar agora</a>',
                    extra_tags='safe'
                )
                request.session[session_key] = True
        else:
            # Assinatura será renovada
            if days <= 3 and not request.session.get(session_key):
                messages.info(
                    request,
                    f'ℹ️ Sua assinatura será renovada em {days} dia(s).'
                )
                request.session[session_key] = True
    
    def _check_class_limit_warning(self, request, subscription):
        """
        Avisa sobre limite de turmas
        """
        max_classes = subscription.total_classes_allowed
        
        # Ilimitado, não precisa avisar
        if max_classes == float('inf'):
            return
        
        current_classes = 0
        try:
            # ===== CORRIGIDO: Importa de classes.models =====
            from classes.models import Class
            current_classes = Class.objects.filter(teacher=request.user).count()
            remaining = max_classes - current_classes
            
            # Atingiu o limite
            if remaining <= 0:
                if not request.session.get('warned_class_limit_reached'):
                    messages.error(
                        request,
                        f'🚫 Você atingiu o limite de {int(max_classes)} turmas do seu plano. '
                        f'<a href="/payments/subscription/" class="alert-link">Adicionar turmas extras</a>',
                        extra_tags='safe'
                    )
                    request.session['warned_class_limit_reached'] = True
            
            # Próximo do limite (2 ou menos)
            elif remaining <= 2 and remaining > 0:
                if not request.session.get(f'warned_class_limit_{int(remaining)}'):
                    messages.warning(
                        request,
                        f'⚠️ Você tem apenas {int(remaining)} turma(s) restante(s) no seu plano.'
                    )
                    request.session[f'warned_class_limit_{int(remaining)}'] = True
            else:
                # Limpa avisos se tiver espaço
                if 'warned_class_limit_reached' in request.session:
                    del request.session['warned_class_limit_reached']
        
        except (ImportError, AttributeError):
            # Modelo Class não existe ainda
            pass
        except Exception as e:
            # Qualquer outro erro - apenas loga
            logger.error(f"Erro ao verificar limite de turmas: {e}")
    
    def _check_payment_status(self, request, subscription):
        """
        Avisa sobre problemas de pagamento
        """
        if subscription.status == 'past_due':
            if not request.session.get('warned_past_due'):
                messages.error(
                    request,
                    '🚫 <strong>Pagamento em atraso!</strong> '
                    'Sua assinatura será cancelada se o pagamento não for efetuado. '
                    '<a href="/payments/portal/" class="alert-link">Atualizar forma de pagamento</a>',
                    extra_tags='safe'
                )
                request.session['warned_past_due'] = True
        
        elif subscription.status == 'unpaid':
            if not request.session.get('warned_unpaid'):
                messages.error(
                    request,
                    '🚫 <strong>Assinatura não paga!</strong> '
                    '<a href="/payments/portal/" class="alert-link">Efetuar pagamento</a>',
                    extra_tags='safe'
                )
                request.session['warned_unpaid'] = True


class SubscriptionAccessMiddleware(MiddlewareMixin):
    """
    Middleware que bloqueia acesso a certas URLs se não tiver assinatura
    (opcional - use apenas se quiser bloqueio automático)
    """
    
    # URLs que exigem assinatura (adicione conforme necessário)
    PROTECTED_PATHS = [
        '/dashboard/',
        '/classes/',
        '/tests/',
        '/students/',
        '/reports/',
    ]
    
    # URLs que são sempre acessíveis
    ALLOWED_PATHS = [
        '/payments/',
        '/login/',
        '/logout/',
        '/register/',
        '/admin/',
        '/static/',
        '/media/',
        '/',  # Homepage
    ]
    
    def process_request(self, request):
        """
        Verifica se o usuário tem permissão para acessar a URL
        """
        # Não verifica para usuários não autenticados (deixa para LoginRequiredMixin)
        if not request.user.is_authenticated:
            return None
        
        # Verifica se a URL precisa de proteção
        path = request.path
        
        # URLs sempre permitidas
        for allowed_path in self.ALLOWED_PATHS:
            if path.startswith(allowed_path):
                return None
        
        # Verifica se precisa de assinatura
        needs_subscription = False
        for protected_path in self.PROTECTED_PATHS:
            if path.startswith(protected_path):
                needs_subscription = True
                break
        
        if not needs_subscription:
            return None
        
        # Verifica se tem assinatura
        subscription = getattr(request, 'subscription', None)
        
        if not subscription:
            messages.warning(
                request,
                'Esta funcionalidade requer uma assinatura ativa. '
                '<a href="/payments/plans/">Ver planos</a>',
                extra_tags='safe'
            )
            from django.shortcuts import redirect
            return redirect('/payments/plans/')
        
        return None


class SubscriptionCacheMiddleware(MiddlewareMixin):
    """
    Middleware para limpar cache quando necessário
    """
    
    def process_response(self, request, response):
        """
        Limpa cache de assinatura quando necessário
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Limpa cache se houver mudança na assinatura
            if request.path.startswith('/payments/') and request.method == 'POST':
                cache_key = f'subscription_{request.user.id}'
                cache.delete(cache_key)
                logger.info(f"Cache de assinatura limpo para usuário {request.user.username}")
        
        return response