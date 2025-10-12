from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

def generate_activation_token():
    return uuid.uuid4()

def get_token_expiry():
    return timezone.now() + timedelta(days=7)

class CustomUser(AbstractUser):
    """
    Modelo de usuário customizado que usa email como identificador único
    e inclui funcionalidades de verificação de email.
    """
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("Um usuário com este email já existe."),
        }
    )
    email_verified = models.BooleanField(
        _('email verificado'),
        default=False,
        help_text=_('Indica se o email do usuário foi verificado.')
    )
    activation_token = models.UUIDField(
        _('token de ativação'),
        default=generate_activation_token,
        editable=False,
        help_text=_('Token usado para verificação de email.')
    )
    activation_token_expiry = models.DateTimeField(
        _('data de expiração do token'),
        null=True,
        blank=True,
        help_text=_('Data de expiração do token de ativação.')
    )
    is_teacher = models.BooleanField(
        _('é professor'),
        default=True,
        help_text=_('Indica se o usuário é um professor.')
    )
    date_joined = models.DateTimeField(
        _('data de cadastro'),
        default=timezone.now
    )
    last_login = models.DateTimeField(
        _('último login'),
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('usuário')
        verbose_name_plural = _('usuários')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def generate_username_from_email(self):
        """
        Gera um username único baseado no email do usuário.
        """
        base_username = self.email.split('@')[0]
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que o username seja gerado
        a partir do email e o token de ativação tenha uma data de expiração.
        """
        if not self.username:
            self.username = self.generate_username_from_email()
        if not self.activation_token_expiry:
            self.activation_token_expiry = get_token_expiry()
        super().save(*args, **kwargs)

    def generate_new_activation_token(self):
        """
        Gera um novo token de ativação e atualiza sua data de expiração.
        """
        self.activation_token = generate_activation_token()
        self.activation_token_expiry = get_token_expiry()
        self.save(update_fields=['activation_token', 'activation_token_expiry'])

    def is_token_valid(self):
        """
        Verifica se o token de ativação ainda é válido.
        """
        if not self.activation_token_expiry:
            return False
        return timezone.now() <= self.activation_token_expiry

    def verify_email(self):
        """
        Marca o email do usuário como verificado.
        """
        self.email_verified = True
        self.save(update_fields=['email_verified'])

    def get_full_name(self):
        """
        Retorna o nome completo do usuário.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """
        Retorna o primeiro nome do usuário ou o email se não houver nome.
        """
        return self.first_name or self.email.split('@')[0]