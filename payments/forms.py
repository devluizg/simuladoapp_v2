# payments/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Plan, Subscription, Payment


class PlanSelectionForm(forms.Form):
    """
    Formulário para seleção de plano
    """
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        label='Escolha seu plano',
        empty_label=None
    )
    
    billing_period = forms.ChoiceField(
        choices=[
            ('monthly', 'Mensal'),
            ('semester', 'Semestral (Economize 10%)'),
            ('annual', 'Anual (Economize 20%)'),
        ],
        widget=forms.RadioSelect,
        label='Período de cobrança',
        initial='semester'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label='Aceito os termos de serviço e política de privacidade',
        error_messages={
            'required': 'Você deve aceitar os termos para continuar.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        plan_type = kwargs.pop('plan_type', None)
        super().__init__(*args, **kwargs)
        
        if plan_type:
            self.fields['plan'].queryset = Plan.objects.filter(
                is_active=True,
                plan_type=plan_type
            )
    
    def clean_plan(self):
        plan = self.cleaned_data.get('plan')
        
        if not plan.is_active:
            raise ValidationError('Este plano não está mais disponível.')
        
        return plan


class ExtraClassesForm(forms.Form):
    """
    Formulário para adicionar turmas extras
    """
    extra_classes = forms.IntegerField(
        min_value=1,
        max_value=50,
        label='Quantidade de turmas extras',
        help_text='Cada turma extra custa R$ 5,00/mês',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite a quantidade'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.subscription = kwargs.pop('subscription', None)
        super().__init__(*args, **kwargs)
        
        if self.subscription and self.subscription.plan.extra_class_price:
            price = self.subscription.plan.extra_class_price
            self.fields['extra_classes'].help_text = f'Cada turma extra custa R$ {price}/mês'
    
    def clean_extra_classes(self):
        quantity = self.cleaned_data.get('extra_classes')
        
        if quantity <= 0:
            raise ValidationError('Quantidade deve ser maior que zero.')
        
        return quantity
    
    def get_total_price(self):
        """Calcula o preço total das turmas extras"""
        if not self.is_valid() or not self.subscription:
            return 0
        
        quantity = self.cleaned_data.get('extra_classes')
        price = self.subscription.plan.extra_class_price or 0
        
        return quantity * price


class CancelSubscriptionForm(forms.Form):
    """
    Formulário para cancelamento de assinatura
    """
    CANCEL_REASONS = [
        ('too_expensive', 'Muito caro'),
        ('not_using', 'Não estou usando'),
        ('missing_features', 'Faltam recursos que preciso'),
        ('technical_issues', 'Problemas técnicos'),
        ('switching_service', 'Mudando para outro serviço'),
        ('temporary', 'Pausa temporária'),
        ('other', 'Outro motivo'),
    ]
    
    cancel_immediately = forms.BooleanField(
        required=False,
        initial=False,
        label='Cancelar imediatamente',
        help_text='Se marcado, cancela agora. Caso contrário, cancela apenas no fim do período pago.'
    )
    
    reason = forms.ChoiceField(
        choices=CANCEL_REASONS,
        widget=forms.RadioSelect,
        label='Motivo do cancelamento',
        required=True
    )
    
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Conte-nos mais sobre sua decisão (opcional)'
        }),
        required=False,
        label='Feedback adicional',
        max_length=500
    )
    
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que desejo cancelar minha assinatura',
        error_messages={
            'required': 'Você deve confirmar o cancelamento.'
        }
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not cleaned_data.get('confirm'):
            raise ValidationError('Você precisa confirmar o cancelamento.')
        
        return cleaned_data


class UpgradePlanForm(forms.Form):
    """
    Formulário para upgrade de plano
    """
    new_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        label='Novo plano',
        empty_label=None
    )
    
    proration_accepted = forms.BooleanField(
        required=True,
        label='Entendo que serei cobrado proporcionalmente pela diferença',
        help_text='Você pagará apenas a diferença proporcional ao tempo restante do período atual.'
    )
    
    def __init__(self, *args, **kwargs):
        current_plan = kwargs.pop('current_plan', None)
        super().__init__(*args, **kwargs)
        
        if current_plan:
            # Mostra apenas planos superiores ao atual
            self.fields['new_plan'].queryset = Plan.objects.filter(
                is_active=True,
                price__gt=current_plan.price
            ).order_by('price')
    
    def clean_new_plan(self):
        new_plan = self.cleaned_data.get('new_plan')
        
        if not new_plan.is_active:
            raise ValidationError('Este plano não está disponível.')
        
        return new_plan


class DowngradePlanForm(forms.Form):
    """
    Formulário para downgrade de plano
    """
    new_plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        label='Novo plano',
        empty_label=None
    )
    
    apply_at_period_end = forms.BooleanField(
        required=False,
        initial=True,
        label='Aplicar mudança apenas no próximo período',
        help_text='Recomendado: a mudança ocorrerá quando seu período atual terminar.'
    )
    
    confirm_data_loss = forms.BooleanField(
        required=True,
        label='Entendo que posso perder acesso a algumas funcionalidades',
        error_messages={
            'required': 'Você deve confirmar que entende as limitações do novo plano.'
        }
    )
    
    def __init__(self, *args, **kwargs):
        current_plan = kwargs.pop('current_plan', None)
        super().__init__(*args, **kwargs)
        
        if current_plan:
            # Mostra apenas planos inferiores ao atual
            self.fields['new_plan'].queryset = Plan.objects.filter(
                is_active=True,
                price__lt=current_plan.price
            ).order_by('-price')
    
    def clean_new_plan(self):
        new_plan = self.cleaned_data.get('new_plan')
        
        if not new_plan.is_active:
            raise ValidationError('Este plano não está disponível.')
        
        return new_plan


class PaymentMethodForm(forms.Form):
    """
    Formulário para informações de pagamento
    (Usado com Stripe Elements no frontend)
    """
    cardholder_name = forms.CharField(
        max_length=100,
        label='Nome no cartão',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome como aparece no cartão'
        })
    )
    
    save_card = forms.BooleanField(
        required=False,
        initial=True,
        label='Salvar este cartão para pagamentos futuros'
    )
    
    # O número do cartão será capturado pelo Stripe Elements
    # Este campo é apenas para o token do Stripe
    stripe_token = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )


class PaymentFilterForm(forms.Form):
    """
    Formulário para filtrar histórico de pagamentos
    """
    STATUS_CHOICES = [
        ('', 'Todos os status'),
        ('succeeded', 'Pagos'),
        ('pending', 'Pendentes'),
        ('failed', 'Falhou'),
        ('refunded', 'Reembolsados'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label='Status',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        label='De',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Até',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError('Data inicial não pode ser maior que data final.')
        
        return cleaned_data


class ContactSupportForm(forms.Form):
    """
    Formulário para contato com suporte (para assinantes premium)
    """
    SUBJECT_CHOICES = [
        ('technical', 'Problema técnico'),
        ('billing', 'Dúvida sobre cobrança'),
        ('feature', 'Solicitação de recurso'),
        ('account', 'Questão da conta'),
        ('other', 'Outro assunto'),
    ]
    
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        label='Assunto',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Baixa'),
            ('medium', 'Média'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        initial='medium',
        label='Prioridade',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'form-control',
            'placeholder': 'Descreva sua questão ou problema...'
        }),
        label='Mensagem',
        max_length=2000
    )
    
    attachment = forms.FileField(
        required=False,
        label='Anexo (opcional)',
        help_text='PNG, JPG ou PDF até 5MB',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Valida tamanho (5MB)
            if attachment.size > 5 * 1024 * 1024:
                raise ValidationError('Arquivo muito grande. Máximo 5MB.')
            
            # Valida tipo
            allowed_types = ['image/png', 'image/jpeg', 'application/pdf']
            if attachment.content_type not in allowed_types:
                raise ValidationError('Tipo de arquivo não permitido. Use PNG, JPG ou PDF.')
        
        return attachment


class ReactivateSubscriptionForm(forms.Form):
    """
    Formulário para reativar assinatura cancelada
    """
    confirm = forms.BooleanField(
        required=True,
        label='Confirmo que desejo reativar minha assinatura',
        error_messages={
            'required': 'Você deve confirmar a reativação.'
        }
    )
    
    update_payment_method = forms.BooleanField(
        required=False,
        initial=False,
        label='Atualizar forma de pagamento',
        help_text='Marque se deseja usar um novo cartão de crédito.'
    )


class PlanComparisonFilterForm(forms.Form):
    """
    Formulário para filtrar comparação de planos
    """
    plan_type = forms.ChoiceField(
        choices=[
            ('', 'Todos os tipos'),
            ('professor', 'Plano Professor'),
            ('institucional', 'Plano Institucional'),
        ],
        required=False,
        label='Tipo de plano',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    billing_period = forms.ChoiceField(
        choices=[
            ('', 'Todos os períodos'),
            ('monthly', 'Mensal'),
            ('semester', 'Semestral'),
            ('annual', 'Anual'),
        ],
        required=False,
        label='Período',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class InvoiceRequestForm(forms.Form):
    """
    Formulário para solicitar segunda via de nota fiscal
    """
    payment = forms.ModelChoiceField(
        queryset=Payment.objects.filter(status='succeeded'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Selecione o pagamento',
        empty_label='Escolha um pagamento'
    )
    
    email = forms.EmailField(
        label='Email para envio',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'seu@email.com'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['payment'].queryset = Payment.objects.filter(
                user=user,
                status='succeeded'
            ).order_by('-created_at')
            
            # Pré-preenche com email do usuário
            if user.email:
                self.fields['email'].initial = user.email


# ========== FORMULÁRIOS PARA ADMIN ==========

class BulkPlanUpdateForm(forms.Form):
    """
    Formulário para atualizar múltiplos planos (apenas admin)
    """
    is_active = forms.NullBooleanField(
        required=False,
        label='Status',
        widget=forms.Select(choices=[
            (None, 'Não alterar'),
            (True, 'Ativar'),
            (False, 'Desativar'),
        ])
    )
    
    is_popular = forms.NullBooleanField(
        required=False,
        label='Mais popular',
        widget=forms.Select(choices=[
            (None, 'Não alterar'),
            (True, 'Marcar como popular'),
            (False, 'Desmarcar como popular'),
        ])
    )


class SubscriptionNoteForm(forms.Form):
    """
    Formulário para adicionar notas internas sobre assinatura
    """
    note = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Adicione uma nota sobre esta assinatura...'
        }),
        label='Nota interna',
        max_length=500
    )