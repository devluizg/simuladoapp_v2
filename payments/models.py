# payments/models.py
from django.db import models
from django.conf import settings  # ← ADICIONE ISTO
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

class Plan(models.Model):
    """Modelo para os planos de assinatura"""
    
    PLAN_TYPE_CHOICES = [
        ('professor', 'Plano Professor'),
        ('institucional', 'Plano Institucional'),
    ]
    
    BILLING_PERIOD_CHOICES = [
        ('monthly', 'Mensal'),
        ('semester', 'Semestral'),
        ('annual', 'Anual'),
    ]
    
    name = models.CharField(_('Nome do Plano'), max_length=100)
    slug = models.SlugField(_('Slug'), unique=True)
    plan_type = models.CharField(_('Tipo de Plano'), max_length=20, choices=PLAN_TYPE_CHOICES)
    billing_period = models.CharField(_('Período de Cobrança'), max_length=20, choices=BILLING_PERIOD_CHOICES)
    
    price = models.DecimalField(_('Preço'), max_digits=10, decimal_places=2)
    
    # Stripe IDs
    stripe_product_id = models.CharField(_('Stripe Product ID'), max_length=255, blank=True)
    stripe_price_id = models.CharField(_('Stripe Price ID'), max_length=255, blank=True)
    
    # Limites e features
    max_classes = models.IntegerField(_('Máximo de Turmas'), null=True, blank=True, 
                                      help_text="Deixe em branco para ilimitado")
    extra_class_price = models.DecimalField(_('Preço por Turma Extra'), 
                                           max_digits=10, decimal_places=2, 
                                           null=True, blank=True)
    
    # Features
    personalized_question_bank = models.BooleanField(_('Banco de Questões Personalizado'), default=True)
    max_test_versions = models.IntegerField(_('Máximo de Versões de Simulado'), default=5)
    automatic_correction = models.BooleanField(_('Correção Automática'), default=True)
    performance_dashboard = models.BooleanField(_('Dashboard de Desempenho'), default=True)
    custom_student_app = models.BooleanField(_('App Personalizado do Aluno'), default=False)
    advanced_reports = models.BooleanField(_('Relatórios Avançados'), default=False)
    priority_support = models.BooleanField(_('Suporte Prioritário'), default=False)
    
    is_active = models.BooleanField(_('Ativo'), default=True)
    is_popular = models.BooleanField(_('Mais Popular'), default=False)
    
    description = models.TextField(_('Descrição'), blank=True)
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Plano')
        verbose_name_plural = _('Planos')
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - R${self.price}/{self.get_billing_period_display()}"
    
    def get_features_list(self):
        """Retorna lista de features ativas"""
        features = []
        if self.max_classes:
            features.append(f"Cadastro de até {self.max_classes} turmas")
        else:
            features.append("Turmas ilimitadas")
        
        if self.personalized_question_bank:
            features.append("Banco de questões personalizado")
        
        if self.max_test_versions:
            features.append(f"Criação de simulados com até {self.max_test_versions} versões")
        
        if self.automatic_correction:
            features.append("Correção automática via aplicativo")
        
        if self.performance_dashboard:
            features.append("Dashboard de desempenho")
        
        if self.custom_student_app:
            features.append("Aplicativo do aluno personalizado com a identidade da instituição")
        
        if self.advanced_reports:
            features.append("Relatórios avançados de desempenho")
        
        if self.priority_support:
            features.append("Suporte prioritário e integração")
        
        if self.extra_class_price:
            features.append(f"Adicional de R${self.extra_class_price} por turma extra")
        
        return features


class Subscription(models.Model):
    """Modelo para as assinaturas dos usuários"""
    
    STATUS_CHOICES = [
        ('incomplete', 'Incompleta'),
        ('incomplete_expired', 'Incompleta Expirada'),
        ('trialing', 'Em Período de Teste'),
        ('active', 'Ativa'),
        ('past_due', 'Vencida'),
        ('canceled', 'Cancelada'),
        ('unpaid', 'Não Paga'),
    ]
    
    # ===== CORRIGIDO: use settings.AUTH_USER_MODEL =====
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    
    # Stripe IDs
    stripe_subscription_id = models.CharField(_('Stripe Subscription ID'), max_length=255, unique=True, null=True, blank=True)
    stripe_customer_id = models.CharField(_('Stripe Customer ID'), max_length=255)
    
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES, default='incomplete')
    
    # Datas
    current_period_start = models.DateTimeField(_('Início do Período Atual'), null=True, blank=True)
    current_period_end = models.DateTimeField(_('Fim do Período Atual'), null=True, blank=True)
    cancel_at_period_end = models.BooleanField(_('Cancelar no Fim do Período'), default=False)
    canceled_at = models.DateTimeField(_('Cancelada em'), null=True, blank=True)
    ended_at = models.DateTimeField(_('Finalizada em'), null=True, blank=True)
    
    # Extras
    extra_classes = models.IntegerField(_('Turmas Extras'), default=0)
    
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Assinatura')
        verbose_name_plural = _('Assinaturas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"
    
    @property
    def is_active(self):
        """Verifica se a assinatura está ativa"""
        return self.status in ['active', 'trialing']
    
    @property
    def is_valid(self):
        """Verifica se a assinatura está válida e não expirada"""
        if not self.is_active:
            return False
        if self.current_period_end and self.current_period_end < timezone.now():
            return False
        return True
    
    @property
    def total_classes_allowed(self):
        """Retorna o total de turmas permitidas (plano + extras)"""
        if self.plan.max_classes is None:  # Ilimitado
            return float('inf')
        return self.plan.max_classes + self.extra_classes
    
    @property
    def days_until_renewal(self):
        """Dias até a renovação"""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - timezone.now()
        return delta.days
    
    def can_create_class(self, current_classes_count):
        """Verifica se o usuário pode criar mais turmas"""
        if not self.is_valid:
            return False
        return current_classes_count < self.total_classes_allowed
    
    def has_feature(self, feature_name):
        """Verifica se o plano tem uma feature específica"""
        return getattr(self.plan, feature_name, False)


class Payment(models.Model):
    """Modelo para registrar os pagamentos"""
    
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('succeeded', 'Sucesso'),
        ('failed', 'Falhou'),
        ('refunded', 'Reembolsado'),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    
    # ===== CORRIGIDO: use settings.AUTH_USER_MODEL =====
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    
    stripe_payment_intent_id = models.CharField(_('Stripe Payment Intent ID'), max_length=255, unique=True, null=True, blank=True)
    stripe_invoice_id = models.CharField(_('Stripe Invoice ID'), max_length=255, blank=True)
    stripe_charge_id = models.CharField(_('Stripe Charge ID'), max_length=255, blank=True)
    
    amount = models.DecimalField(_('Valor'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Moeda'), max_length=3, default='BRL')
    status = models.CharField(_('Status'), max_length=20, choices=STATUS_CHOICES)
    
    description = models.TextField(_('Descrição'), blank=True)
    
    paid_at = models.DateTimeField(_('Pago em'), null=True, blank=True)
    created_at = models.DateTimeField(_('Criado em'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Atualizado em'), auto_now=True)
    
    class Meta:
        verbose_name = _('Pagamento')
        verbose_name_plural = _('Pagamentos')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"R${self.amount} - {self.user.username} ({self.status})"


class StripeWebhookEvent(models.Model):
    """Modelo para registrar eventos do webhook do Stripe"""
    
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    data = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Evento Webhook Stripe'
        verbose_name_plural = 'Eventos Webhook Stripe'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id}"