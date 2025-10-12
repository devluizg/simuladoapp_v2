# Salve este conteúdo como /home/devluizg/simuladoapp/api/serializers_auth.py
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Especificar que queremos usar email para autenticação em vez de username
    username_field = 'email'

    # Adicionar campos extras para validação
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'] = serializers.CharField(
            style={'input_type': 'password'},
            trim_whitespace=False
        )
        # Remova o campo username se existir e adicione email
        if 'username' in self.fields:
            del self.fields['username']
        self.fields['email'] = serializers.EmailField()

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Adicionar dados personalizados ao token
        token['email'] = user.email
        token['name'] = user.get_full_name() or user.email
        return token

    def validate(self, attrs):
        # Log para debug
        print(f"Tentativa de login com: {attrs}")

        # Salvar email para usar na validação
        email = attrs.get('email')

        # Remover qualquer campo username
        if 'username' in attrs:
            del attrs['username']

        # Incluir o email como username para o validador pai
        attrs[self.username_field] = email

        return super().validate(attrs)