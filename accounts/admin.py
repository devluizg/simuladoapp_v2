# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_active', 
                   'email_verified', 'date_joined', 'last_login')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'email_verified')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Campos mostrados ao editar um usuário existente
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': ('username', 'first_name', 'last_name')
        }),
        (_('Verification'), {
            'fields': ('email_verified', 'activation_token', 'activation_token_expiry')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Campos mostrados ao adicionar um novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('activation_token', 'date_joined', 'last_login')
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Use o CustomUserCreationForm apenas para adicionar novos usuários
        """
        if not obj:
            kwargs['form'] = CustomUserCreationForm
        return super().get_form(request, obj, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        Garante que o username seja gerado corretamente ao salvar no admin
        """
        if not obj.username:
            obj.username = obj.generate_username_from_email()
        super().save_model(request, obj, form, change)

    # Ações personalizadas
    actions = ['verify_email', 'unverify_email']

    def verify_email(self, request, queryset):
        queryset.update(email_verified=True)
    verify_email.short_description = "Marcar emails selecionados como verificados"

    def unverify_email(self, request, queryset):
        queryset.update(email_verified=False)
    unverify_email.short_description = "Marcar emails selecionados como não verificados"

    # Customização da exibição
    def get_readonly_fields(self, request, obj=None):
        """
        Torna alguns campos somente leitura após a criação
        """
        if obj:  # Editando um usuário existente
            return self.readonly_fields + ('email',)
        return self.readonly_fields

    def get_fieldsets(self, request, obj=None):
        """
        Customiza os fieldsets baseado se está criando ou editando
        """
        if not obj:  # Criando um novo usuário
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
