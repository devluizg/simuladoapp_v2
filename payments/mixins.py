# payments/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
import logging

from .permissions import get_user_subscription

logger = logging.getLogger('payments')


class SubscriptionRequiredMixin(LoginRequiredMixin):
    """
    Mixin que exige assinatura ativa para Class-Based Views
    
    Usage:
        class MyView(SubscriptionRequiredMixin, TemplateView):
            template_name = 'my_template.html'
    """
    
    subscription_required_message = 'Você precisa de uma assinatura ativa para acessar esta página.'
    subscription_redirect_url = '/payments/plans/'
    raise_exception = False  # Se True, levanta PermissionDenied ao invés de redirecionar
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            if self.raise_exception:
                raise PermissionDenied(self.subscription_required_message)
            
            messages.warning(request, self.subscription_required_message)
            return redirect(self.subscription_redirect_url)
        
        # Adiciona ao request
        self.request.subscription = subscription
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Adiciona subscription ao contexto"""
        context = super().get_context_data(**kwargs)
        context['subscription'] = getattr(self.request, 'subscription', None)
        return context


class FeatureRequiredMixin(SubscriptionRequiredMixin):
    """
    Mixin que exige uma feature específica do plano
    
    Usage:
        class AdvancedReportsView(FeatureRequiredMixin, TemplateView):
            required_feature = 'advanced_reports'
            template_name = 'reports.html'
    """
    
    required_feature = None  # Defina na sua view (ex: 'custom_student_app')
    feature_required_message = 'Esta funcionalidade não está disponível no seu plano atual.'
    feature_redirect_url = '/payments/subscription/'
    
    def dispatch(self, request, *args, **kwargs):
        # Primeiro verifica se tem assinatura
        response = super().dispatch(request, *args, **kwargs)
        
        # Se retornou um redirect do parent, retorna
        if not hasattr(response, 'render'):
            return response
        
        # Verifica a feature
        if not self.required_feature:
            raise ValueError("required_feature não foi definido na view")
        
        subscription = getattr(request, 'subscription', None)
        
        if not subscription or not subscription.has_feature(self.required_feature):
            if self.raise_exception:
                raise PermissionDenied(self.feature_required_message)
            
            messages.warning(request, self.feature_required_message)
            return redirect(self.feature_redirect_url)
        
        return response


class ClassLimitMixin(SubscriptionRequiredMixin):
    """
    Mixin que verifica limite de turmas
    
    Usage:
        class CreateClassView(ClassLimitMixin, CreateView):
            model = Class
            ...
    """
    
    class_limit_message = 'Você atingiu o limite de turmas do seu plano.'
    class_limit_redirect_url = '/payments/subscription/'
    
    def dispatch(self, request, *args, **kwargs):
        # Primeiro verifica se tem assinatura
        response = super().dispatch(request, *args, **kwargs)
        
        if not hasattr(response, 'render'):
            return response
        
        subscription = getattr(request, 'subscription', None)
        
        # Verifica limite de turmas
        current_classes = 0
        try:
            # ===== CORRIGIDO: Importa de classes.models =====
            from classes.models import Class
            current_classes = Class.objects.filter(teacher=request.user).count()
            
            if not subscription.can_create_class(current_classes):
                if self.raise_exception:
                    raise PermissionDenied(self.class_limit_message)
                
                messages.warning(request, self.class_limit_message)
                return redirect(self.class_limit_redirect_url)
            
            # Adiciona ao request
            request.current_classes_count = current_classes
            remaining = subscription.total_classes_allowed - current_classes
            request.remaining_classes = remaining if remaining != float('inf') else -1
            
        except (ImportError, AttributeError):
            # Modelo não existe ainda - permite passar
            pass
        except Exception as e:
            # Qualquer outro erro - loga e permite passar
            logger.error(f"Erro ao verificar limite de turmas no mixin: {e}")
        
        return response
    
    def get_context_data(self, **kwargs):
        """Adiciona informações de limite ao contexto"""
        context = super().get_context_data(**kwargs)
        context['current_classes_count'] = getattr(self.request, 'current_classes_count', 0)
        context['remaining_classes'] = getattr(self.request, 'remaining_classes', 0)
        return context


class PlanTypeMixin:
    """
    Mixin que filtra planos por tipo
    
    Usage:
        class InstitutionalPlansView(PlanTypeMixin, ListView):
            plan_type = 'institucional'
            model = Plan
    """
    
    plan_type = None  # 'professor' ou 'institucional'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.plan_type:
            queryset = queryset.filter(plan_type=self.plan_type)
        
        return queryset.filter(is_active=True)


class AjaxRequiredMixin:
    """
    Mixin que exige que a requisição seja AJAX
    
    Usage:
        class MyAjaxView(AjaxRequiredMixin, View):
            ...
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'error': 'Esta view requer uma requisição AJAX'
            }, status=400)
        
        return super().dispatch(request, *args, **kwargs)


class SubscriptionOwnerMixin(UserPassesTestMixin):
    """
    Mixin que garante que o usuário é dono da assinatura
    
    Usage:
        class SubscriptionDetailView(SubscriptionOwnerMixin, DetailView):
            model = Subscription
    """
    
    def test_func(self):
        subscription = self.get_object()
        return subscription.user == self.request.user


class PaymentOwnerMixin(UserPassesTestMixin):
    """
    Mixin que garante que o usuário é dono do pagamento
    
    Usage:
        class PaymentDetailView(PaymentOwnerMixin, DetailView):
            model = Payment
    """
    
    def test_func(self):
        payment = self.get_object()
        return payment.user == self.request.user


class SubscriptionContextMixin:
    """
    Mixin que adiciona informações de assinatura ao contexto
    Útil para adicionar em qualquer view
    
    Usage:
        class MyView(SubscriptionContextMixin, TemplateView):
            template_name = 'my_template.html'
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            subscription = get_user_subscription(self.request.user)
            
            context['subscription'] = subscription
            context['has_subscription'] = subscription is not None
            
            if subscription:
                context['subscription_plan'] = subscription.plan
                context['subscription_features'] = {
                    'personalized_question_bank': subscription.plan.personalized_question_bank,
                    'max_test_versions': subscription.plan.max_test_versions,
                    'automatic_correction': subscription.plan.automatic_correction,
                    'performance_dashboard': subscription.plan.performance_dashboard,
                    'custom_student_app': subscription.plan.custom_student_app,
                    'advanced_reports': subscription.plan.advanced_reports,
                    'priority_support': subscription.plan.priority_support,
                }
        
        return context


class ActiveSubscriptionRequiredMixin(SubscriptionRequiredMixin):
    """
    Mixin que exige assinatura ativa E válida (não expirada)
    
    Usage:
        class PremiumFeatureView(ActiveSubscriptionRequiredMixin, TemplateView):
            ...
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        if not hasattr(response, 'render'):
            return response
        
        subscription = getattr(request, 'subscription', None)
        
        if subscription and not subscription.is_valid:
            messages.error(
                request,
                'Sua assinatura expirou ou está com pagamento pendente. '
                'Por favor, regularize sua situação.'
            )
            return redirect('/payments/subscription/')
        
        return response


# ========== MIXINS COMBINADOS ==========

class PremiumFeatureMixin(FeatureRequiredMixin, ActiveSubscriptionRequiredMixin):
    """
    Mixin combinado que exige assinatura ativa + feature específica
    
    Usage:
        class CustomAppView(PremiumFeatureMixin, TemplateView):
            required_feature = 'custom_student_app'
            template_name = 'custom_app.html'
    """
    pass


class CreateClassMixin(ClassLimitMixin, ActiveSubscriptionRequiredMixin):
    """
    Mixin combinado para criação de turmas
    
    Usage:
        class CreateClassView(CreateClassMixin, CreateView):
            model = Class
            ...
    """
    pass