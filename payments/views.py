# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, TemplateView, View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.conf import settings
from django.db.models import Q

from .models import Plan, Subscription, Payment
from .services import StripeService
from .permissions import get_user_subscription

import json
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


# ========== VIEWS DE PLANOS ==========

class PlansListView(ListView):
    """Lista todos os planos disponíveis"""
    model = Plan
    template_name = 'payments/plans_list.html'
    context_object_name = 'plans'
    
    def get_queryset(self):
        return Plan.objects.filter(is_active=True).order_by('price')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Separa planos por tipo
        context['professor_plans'] = self.get_queryset().filter(plan_type='professor')
        context['institutional_plans'] = self.get_queryset().filter(plan_type='institucional')
        
        # Adiciona assinatura atual do usuário
        if self.request.user.is_authenticated:
            context['current_subscription'] = get_user_subscription(self.request.user)
        
        return context


class PlanDetailView(DetailView):
    """Detalhes de um plano específico"""
    model = Plan
    template_name = 'payments/plan_detail.html'
    context_object_name = 'plan'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['features'] = self.object.get_features_list()
        
        if self.request.user.is_authenticated:
            context['current_subscription'] = get_user_subscription(self.request.user)
        
        return context


# ========== CHECKOUT ==========

class CheckoutView(LoginRequiredMixin, TemplateView):
    """Página de checkout"""
    template_name = 'payments/checkout.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan_slug = self.kwargs.get('plan_slug')
        plan = get_object_or_404(Plan, slug=plan_slug, is_active=True)
        
        context['plan'] = plan
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['features'] = plan.get_features_list()
        
        return context


class CreateCheckoutSessionView(LoginRequiredMixin, View):
    """Cria sessão de checkout no Stripe"""
    
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            plan_slug = data.get('plan_slug')
            
            plan = get_object_or_404(Plan, slug=plan_slug, is_active=True)
            
            # Verifica se já tem assinatura ativa
            existing_subscription = get_user_subscription(request.user)
            if existing_subscription:
                return JsonResponse({
                    'error': 'Você já possui uma assinatura ativa.'
                }, status=400)
            
            # Cria sessão de checkout
            stripe_service = StripeService()
            
            success_url = request.build_absolute_uri(
                reverse('payments:checkout_success')
            ) + '?session_id={CHECKOUT_SESSION_ID}'
            
            cancel_url = request.build_absolute_uri(
                reverse('payments:checkout_cancel')
            )
            
            session = stripe_service.create_checkout_session(
                user=request.user,
                plan=plan,
                success_url=success_url,
                cancel_url=cancel_url
            )
            
            return JsonResponse({
                'sessionId': session.id
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)


class CheckoutSuccessView(LoginRequiredMixin, TemplateView):
    """Página de sucesso após checkout"""
    template_name = 'payments/checkout_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session_id = self.request.GET.get('session_id')
        
        if session_id:
            try:
                session = stripe.checkout.Session.retrieve(session_id)
                context['session'] = session
                context['subscription'] = get_user_subscription(self.request.user)
            except Exception as e:
                context['error'] = str(e)
        
        return context


class CheckoutCancelView(LoginRequiredMixin, TemplateView):
    """Página quando checkout é cancelado"""
    template_name = 'payments/checkout_cancel.html'


# ========== GERENCIAMENTO DE ASSINATURAS ==========

class SubscriptionDetailView(LoginRequiredMixin, TemplateView):
    """Detalhes da assinatura do usuário"""
    template_name = 'payments/subscription_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription = get_user_subscription(self.request.user)
        
        if not subscription:
            return context
        
        context['subscription'] = subscription
        context['plan'] = subscription.plan
        context['features'] = subscription.plan.get_features_list()
        
        # Busca histórico de pagamentos
        context['recent_payments'] = Payment.objects.filter(
            subscription=subscription
        ).order_by('-created_at')[:5]
        
        # Planos disponíveis para upgrade
        context['upgrade_plans'] = Plan.objects.filter(
            is_active=True,
            price__gt=subscription.plan.price
        ).order_by('price')
        
        return context


class CancelSubscriptionView(LoginRequiredMixin, View):
    """Cancela a assinatura do usuário"""
    
    def post(self, request, *args, **kwargs):
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            messages.error(request, 'Você não possui uma assinatura ativa.')
            return redirect('payments:plans_list')
        
        try:
            data = json.loads(request.body) if request.body else {}
            immediately = data.get('immediately', False)
            
            stripe_service = StripeService()
            stripe_service.cancel_subscription(
                subscription.stripe_subscription_id,
                immediately=immediately
            )
            
            if immediately:
                messages.success(request, 'Sua assinatura foi cancelada imediatamente.')
            else:
                messages.success(request, 'Sua assinatura será cancelada no final do período atual.')
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class ReactivateSubscriptionView(LoginRequiredMixin, View):
    """Reativa uma assinatura cancelada"""
    
    def post(self, request, *args, **kwargs):
        subscription = Subscription.objects.filter(
            user=request.user,
            cancel_at_period_end=True
        ).first()
        
        if not subscription:
            return JsonResponse({
                'error': 'Nenhuma assinatura cancelada encontrada.'
            }, status=400)
        
        try:
            stripe_service = StripeService()
            stripe_service.reactivate_subscription(subscription.stripe_subscription_id)
            
            messages.success(request, 'Sua assinatura foi reativada com sucesso!')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


class UpgradeSubscriptionView(LoginRequiredMixin, View):
    """Faz upgrade do plano"""
    
    def post(self, request, *args, **kwargs):
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            return JsonResponse({
                'error': 'Você não possui uma assinatura ativa.'
            }, status=400)
        
        try:
            data = json.loads(request.body)
            new_plan_slug = data.get('plan_slug')
            
            new_plan = get_object_or_404(Plan, slug=new_plan_slug, is_active=True)
            
            # Verifica se é realmente um upgrade
            if new_plan.price <= subscription.plan.price:
                return JsonResponse({
                    'error': 'O novo plano deve ser superior ao atual.'
                }, status=400)
            
            stripe_service = StripeService()
            stripe_service.update_subscription_plan(
                subscription.stripe_subscription_id,
                new_plan
            )
            
            messages.success(request, f'Seu plano foi atualizado para {new_plan.name}!')
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# ========== PORTAL DO CLIENTE ==========

class CustomerPortalView(LoginRequiredMixin, View):
    """Redireciona para o portal do cliente do Stripe"""
    
    def get(self, request, *args, **kwargs):
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            messages.error(request, 'Você não possui uma assinatura ativa.')
            return redirect('payments:plans_list')
        
        try:
            stripe_service = StripeService()
            return_url = request.build_absolute_uri(reverse('payments:subscription_detail'))
            
            session = stripe_service.create_customer_portal_session(
                subscription.stripe_customer_id,
                return_url
            )
            
            return redirect(session.url)
            
        except Exception as e:
            messages.error(request, f'Erro ao acessar portal: {str(e)}')
            return redirect('payments:subscription_detail')


# ========== HISTÓRICO DE PAGAMENTOS ==========

class PaymentHistoryView(LoginRequiredMixin, ListView):
    """Lista histórico de pagamentos do usuário"""
    model = Payment
    template_name = 'payments/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return Payment.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class PaymentDetailView(LoginRequiredMixin, DetailView):
    """Detalhes de um pagamento específico"""
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'
    
    def get_queryset(self):
        # Garante que o usuário só veja seus próprios pagamentos
        return Payment.objects.filter(user=self.request.user)


# ========== WEBHOOK DO STRIPE ==========

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """Recebe e processa webhooks do Stripe"""
    
    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            stripe_service = StripeService()
            event = stripe_service.verify_webhook_signature(payload, sig_header)
            
            # Processa o evento
            result = stripe_service.handle_webhook_event(event)
            
            return HttpResponse(status=200)
            
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return HttpResponse(status=400)


# ========== API ENDPOINTS ==========

class CheckSubscriptionView(LoginRequiredMixin, View):
    """API para verificar status da assinatura"""
    
    def get(self, request, *args, **kwargs):
        subscription = get_user_subscription(request.user)
        
        if not subscription:
            return JsonResponse({
                'has_subscription': False,
                'is_active': False
            })
        
        return JsonResponse({
            'has_subscription': True,
            'is_active': subscription.is_active,
            'is_valid': subscription.is_valid,
            'plan_name': subscription.plan.name,
            'plan_type': subscription.plan.plan_type,
            'status': subscription.status,
            'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            'cancel_at_period_end': subscription.cancel_at_period_end,
            'max_classes': subscription.total_classes_allowed if subscription.total_classes_allowed != float('inf') else None,
        })


class GetPlansAPIView(View):
    """API para buscar planos disponíveis"""
    
    def get(self, request, *args, **kwargs):
        plan_type = request.GET.get('type')
        
        queryset = Plan.objects.filter(is_active=True)
        
        if plan_type:
            queryset = queryset.filter(plan_type=plan_type)
        
        plans_data = []
        for plan in queryset:
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'slug': plan.slug,
                'type': plan.plan_type,
                'billing_period': plan.billing_period,
                'price': float(plan.price),
                'is_popular': plan.is_popular,
                'max_classes': plan.max_classes,
                'features': plan.get_features_list(),
            })
        
        return JsonResponse({'plans': plans_data})