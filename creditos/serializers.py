from rest_framework import serializers
from .models import CreditoUsuario


class CreditoUsuarioSerializer(serializers.ModelSerializer):
    creditos_restantes = serializers.ReadOnlyField()
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = CreditoUsuario
        fields = [
            'id',
            'username',
            'total_creditos',
            'usados_creditos',
            'creditos_restantes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'usados_creditos', 'created_at', 'updated_at']


class AdicionarCreditosSerializer(serializers.Serializer):
    quantidade = serializers.IntegerField(
        min_value=1,
        max_value=1000,
        help_text="Quantidade de créditos a adicionar (1-1000)"
    )

    def validate_quantidade(self, value):
        if value <= 0:
            raise serializers.ValidationError("A quantidade deve ser maior que zero.")
        return value


class UsarCreditoSerializer(serializers.Serializer):
    """Serializer para resposta do uso de crédito"""
    sucesso = serializers.BooleanField(read_only=True)
    creditos_restantes = serializers.IntegerField(read_only=True)
    mensagem = serializers.CharField(read_only=True)

class ComprarCreditosSerializer(serializers.Serializer):
    """Serializer para validar dados de compra de créditos"""
    purchase_token = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Token de compra fornecido pelo Google Play"
    )
    produto_id = serializers.CharField(
        max_length=100,
        required=True,
        help_text="ID do produto comprado (ex: creditos_300)"
    )

    def validate_produto_id(self, value):
        """Valida se o produto_id é válido"""
        produtos_validos = ['creditos_300', 'creditos_800', 'creditos_2000']
        if value not in produtos_validos:
            raise serializers.ValidationError(
                f"Produto inválido. Produtos válidos: {produtos_validos}"
            )
        return value