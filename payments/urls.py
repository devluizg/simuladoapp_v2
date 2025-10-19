# payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # ========== PÁGINAS DE PLANOS ==========
    path('plans/', views.PlansListView.as_view(), name='plans_list'),
    path('plans/<slug:slug>/', views.PlanDetailView.as_view(), name='plan_detail'),
    
    # ========== CHECKOUT ==========
    path('checkout/success/', views.CheckoutSuccessView.as_view(), name='checkout_success'),
    path('checkout/cancel/', views.CheckoutCancelView.as_view(), name='checkout_cancel'),
    path('checkout/<slug:plan_slug>/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/session/create/', views.CreateCheckoutSessionView.as_view(), name='create_checkout_session'),
    
    # ========== ASSINATURAS DO USUÁRIO ==========
    path('subscription/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscription/cancel/', views.CancelSubscriptionView.as_view(), name='cancel_subscription'),
    path('subscription/reactivate/', views.ReactivateSubscriptionView.as_view(), name='reactivate_subscription'),
    path('subscription/upgrade/', views.UpgradeSubscriptionView.as_view(), name='upgrade_subscription'),
    
    # ========== PORTAL DO CLIENTE ==========
    path('portal/', views.CustomerPortalView.as_view(), name='customer_portal'),
    
    # ========== HISTÓRICO DE PAGAMENTOS ==========
    path('payments/', views.PaymentHistoryView.as_view(), name='payment_history'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment_detail'),
    
    # ========== WEBHOOKS DO STRIPE ==========
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe_webhook'),
    
    # ========== AJAX/API ==========
    path('api/check-subscription/', views.CheckSubscriptionView.as_view(), name='check_subscription'),
    path('api/get-plans/', views.GetPlansAPIView.as_view(), name='get_plans_api'),
]