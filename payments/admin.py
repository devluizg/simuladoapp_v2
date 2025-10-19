# payments/admin.py
from datetime import timezone
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Plan, Subscription, Payment, StripeWebhookEvent

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'billing_period', 'price_display', 'is_popular', 'is_active', 'stripe_status']
    list_filter = ['plan_type', 'billing_period', 'is_active', 'is_popular']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'slug', 'plan_type', 'billing_period', 'price', 'description')
        }),
        ('Stripe', {
            'fields': ('stripe_product_id', 'stripe_price_id'),
            'classes': ('collapse',)
        }),
        ('Limites', {
            'fields': ('max_classes', 'extra_class_price')
        }),
        ('Features', {
            'fields': (
                'personalized_question_bank',
                'max_test_versions',
                'automatic_correction',
                'performance_dashboard',
                'custom_student_app',
                'advanced_reports',
                'priority_support'
            )
        }),
        ('Status', {
            'fields': ('is_active', 'is_popular')
        }),
    )
    
    def price_display(self, obj):
        return f"R$ {obj.price}"
    price_display.short_description = 'Preço'
    
    def stripe_status(self, obj):
        if obj.stripe_product_id and obj.stripe_price_id:
            return format_html('<span style="color: green;">✓ Configurado</span>')
        return format_html('<span style="color: red;">✗ Não configurado</span>')
    stripe_status.short_description = 'Status Stripe'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'plan', 'status_badge', 'current_period_end', 'cancel_at_period_end', 'created_at']
    list_filter = ['status', 'plan', 'cancel_at_period_end', 'created_at']
    search_fields = ['user__username', 'user__email', 'stripe_subscription_id', 'stripe_customer_id']
    readonly_fields = ['created_at', 'updated_at', 'stripe_subscription_id', 'stripe_customer_id']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações', {
            'fields': ('user', 'plan', 'status', 'extra_classes')
        }),
        ('Stripe', {
            'fields': ('stripe_subscription_id', 'stripe_customer_id'),
            'classes': ('collapse',)
        }),
        ('Período', {
            'fields': ('current_period_start', 'current_period_end', 'cancel_at_period_end', 'canceled_at', 'ended_at')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Usuário'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'trialing': 'blue',
            'canceled': 'red',
            'past_due': 'orange',
            'unpaid': 'red',
            'incomplete': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['cancel_subscriptions']
    
    def cancel_subscriptions(self, request, queryset):
        from .services import StripeService
        stripe_service = StripeService()
        
        count = 0
        for subscription in queryset:
            if subscription.is_active:
                try:
                    stripe_service.cancel_subscription(subscription.stripe_subscription_id)
                    count += 1
                except Exception as e:
                    self.message_user(request, f'Erro ao cancelar {subscription}: {str(e)}', level='error')
        
        self.message_user(request, f'{count} assinatura(s) cancelada(s) com sucesso.')
    cancel_subscriptions.short_description = 'Cancelar assinaturas selecionadas'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_link', 'amount_display', 'status_badge', 'subscription_link', 'paid_at', 'created_at']
    list_filter = ['status', 'currency', 'created_at', 'paid_at']
    search_fields = ['user__username', 'stripe_payment_intent_id', 'stripe_invoice_id']
    readonly_fields = ['created_at', 'updated_at', 'stripe_payment_intent_id', 'stripe_invoice_id', 'stripe_charge_id']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações', {
            'fields': ('user', 'subscription', 'amount', 'currency', 'status', 'description')
        }),
        ('Stripe', {
            'fields': ('stripe_payment_intent_id', 'stripe_invoice_id', 'stripe_charge_id'),
            'classes': ('collapse',)
        }),
        ('Datas', {
            'fields': ('paid_at', 'created_at', 'updated_at')
        }),
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Usuário'
    
    def subscription_link(self, obj):
        if obj.subscription:
            url = reverse('admin:payments_subscription_change', args=[obj.subscription.id])
            return format_html('<a href="{}">#{}</a>', url, obj.subscription.id)
        return '-'
    subscription_link.short_description = 'Assinatura'
    
    def amount_display(self, obj):
        return f"R$ {obj.amount}"
    amount_display.short_description = 'Valor'
    
    def status_badge(self, obj):
        colors = {
            'succeeded': 'green',
            'pending': 'orange',
            'failed': 'red',
            'refunded': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(StripeWebhookEvent)
class StripeWebhookEventAdmin(admin.ModelAdmin):
    list_display = ['stripe_event_id', 'event_type', 'processed_badge', 'created_at', 'processed_at']
    list_filter = ['processed', 'event_type', 'created_at']
    search_fields = ['stripe_event_id', 'event_type']
    readonly_fields = ['stripe_event_id', 'event_type', 'data', 'created_at', 'processed_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações', {
            'fields': ('stripe_event_id', 'event_type', 'processed')
        }),
        ('Dados', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Processamento', {
            'fields': ('error_message', 'processed_at')
        }),
        ('Metadados', {
            'fields': ('created_at',)
        }),
    )
    
    def processed_badge(self, obj):
        if obj.processed:
            return format_html('<span style="color: green;">✓ Processado</span>')
        return format_html('<span style="color: orange;">⏳ Pendente</span>')
    processed_badge.short_description = 'Status'
    
    actions = ['reprocess_events']
    
    def reprocess_events(self, request, queryset):
        from .services import StripeService
        stripe_service = StripeService()
        
        count = 0
        for event in queryset:
            try:
                stripe_service.handle_webhook_event(event.data)
                event.processed = True
                event.processed_at = timezone.now()
                event.error_message = ''
                event.save()
                count += 1
            except Exception as e:
                event.error_message = str(e)
                event.save()
                self.message_user(request, f'Erro ao reprocessar {event}: {str(e)}', level='error')
        
        self.message_user(request, f'{count} evento(s) reprocessado(s) com sucesso.')
    reprocess_events.short_description = 'Reprocessar eventos selecionados'