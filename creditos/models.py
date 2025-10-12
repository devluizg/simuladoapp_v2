from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class CreditoUsuario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credito_usuario',
        verbose_name='Usuário'
    )
    total_creditos = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Total de Créditos'
    )
    usados_creditos = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Créditos Utilizados'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Crédito do Usuário'
        verbose_name_plural = 'Créditos dos Usuários'
        db_table = 'creditos_creditousuario'

    def __str__(self):
        return f'{self.user.username} - {self.creditos_restantes} créditos restantes'

    @property
    def creditos_restantes(self):
        """Calcula a quantidade de créditos restantes do usuário"""
        return max(0, self.total_creditos - self.usados_creditos)

    def pode_usar_credito(self):
        """Verifica se o usuário tem créditos disponíveis"""
        return self.creditos_restantes > 0

    def usar_credito(self):
        """
        Consome um crédito se disponível.
        Retorna True se conseguiu usar, False caso contrário.
        """
        if self.pode_usar_credito():
            self.usados_creditos += 1
            self.save(update_fields=['usados_creditos', 'updated_at'])
            return True
        return False

    def adicionar_creditos(self, quantidade):
        """Adiciona créditos ao total do usuário"""
        if quantidade > 0:
            self.total_creditos += quantidade
            self.save(update_fields=['total_creditos', 'updated_at'])
            return True
        return False

class CompraCredito(models.Model):
    """Modelo para rastrear compras de créditos e evitar duplicatas"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='compras_credito',
        verbose_name='Usuário'
    )
    purchase_token = models.CharField(
        max_length=500,
        unique=True,
        verbose_name='Token de Compra'
    )
    produto_id = models.CharField(
        max_length=100,
        verbose_name='ID do Produto'
    )
    quantidade_creditos = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantidade de Créditos'
    )
    data_compra = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Compra'
    )
    valor_pago = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Valor Pago'
    )
    validada_google = models.BooleanField(
        default=False,
        verbose_name='Validada pelo Google'
    )

    class Meta:
        verbose_name = 'Compra de Crédito'
        verbose_name_plural = 'Compras de Créditos'
        db_table = 'creditos_compracredito'
        ordering = ['-data_compra']

    def __str__(self):
        return f'{self.user.username} - {self.produto_id} - {self.quantidade_creditos} créditos'