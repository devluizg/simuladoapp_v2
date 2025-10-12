# creditos/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import CreditoUsuario, CompraCredito

User = get_user_model()

@admin.register(CreditoUsuario)
class CreditoUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'user_info',
        'total_creditos',
        'usados_creditos',
        'creditos_restantes_display',
        'created_at',
        'actions_links'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at', 'creditos_restantes_display']

    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user',)
        }),
        ('Créditos', {
            'fields': ('total_creditos', 'usados_creditos', 'creditos_restantes_display'),
            'description': 'Você pode editar o total de créditos diretamente aqui.'
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        """Mostra informações do usuário"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_info.short_description = 'Usuário'

    def creditos_restantes_display(self, obj):
        """Mostra créditos restantes com cor"""
        creditos = obj.creditos_restantes
        if creditos > 50:
            color = 'green'
        elif creditos > 10:
            color = 'orange'
        else:
            color = 'red'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} créditos</span>',
            color,
            creditos
        )
    creditos_restantes_display.short_description = 'Créditos Restantes'

    def actions_links(self, obj):
        """Links de ações rápidas"""
        return format_html(
            '<a class="button" href="{}">+50 Créditos</a>&nbsp;'
            '<a class="button" href="{}">+100 Créditos</a>&nbsp;'
            '<a class="button" href="{}">+500 Créditos</a>',
            reverse('admin:add_credits', args=[obj.pk, 50]),
            reverse('admin:add_credits', args=[obj.pk, 100]),
            reverse('admin:add_credits', args=[obj.pk, 500]),
        )
    actions_links.short_description = 'Ações Rápidas'

    def get_urls(self):
        """Adicionar URLs customizadas"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                'add-credits/<int:user_id>/<int:amount>/',
                self.admin_site.admin_view(self.add_credits_view),
                name='add_credits',
            ),
        ]
        return custom_urls + urls

    def add_credits_view(self, request, user_id, amount):
        """View para adicionar créditos rapidamente"""
        try:
            credito_usuario = CreditoUsuario.objects.get(pk=user_id)
            credito_usuario.adicionar_creditos(amount)

            messages.success(
                request,
                f'{amount} créditos adicionados para {credito_usuario.user.username}! '
                f'Total atual: {credito_usuario.creditos_restantes} créditos.'
            )
        except CreditoUsuario.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')

        return HttpResponseRedirect(reverse('admin:creditos_creditousuario_changelist'))

@admin.register(CompraCredito)
class CompraCreditoAdmin(admin.ModelAdmin):
    list_display = [
        'user_info',
        'produto_id',
        'quantidade_creditos',
        'valor_pago',
        'validada_google',
        'data_compra'
    ]
    list_filter = ['validada_google', 'data_compra', 'produto_id']
    search_fields = ['user__username', 'user__email', 'produto_id', 'purchase_token']
    readonly_fields = ['purchase_token', 'data_compra']

    def user_info(self, obj):
        """Mostra informações do usuário"""
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_info.short_description = 'Usuário'

# Ação personalizada para adicionar créditos em lote
def adicionar_creditos_lote(modeladmin, request, queryset):
    """Adicionar créditos para usuários selecionados"""
    from django import forms
    from django.shortcuts import render

    class CreditForm(forms.Form):
        quantidade = forms.IntegerField(
            min_value=1,
            max_value=10000,
            initial=100,
            help_text="Quantidade de créditos para adicionar a cada usuário selecionado"
        )

    if 'apply' in request.POST:
        form = CreditForm(request.POST)
        if form.is_valid():
            quantidade = form.cleaned_data['quantidade']
            usuarios_atualizados = 0

            for credito_usuario in queryset:
                credito_usuario.adicionar_creditos(quantidade)
                usuarios_atualizados += 1

            messages.success(
                request,
                f'{quantidade} créditos adicionados para {usuarios_atualizados} usuários!'
            )
            return HttpResponseRedirect(request.get_full_path())
    else:
        form = CreditForm()

    return render(
        request,
        'admin/adicionar_creditos_lote.html',
        {
            'form': form,
            'usuarios': queryset,
            'action_checkbox_name': admin.ACTION_CHECKBOX_NAME,
        }
    )

adicionar_creditos_lote.short_description = "Adicionar créditos em lote"

# Registrar a ação
CreditoUsuarioAdmin.actions = [adicionar_creditos_lote]