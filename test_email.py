# test_email.py

import os
import django
import sys

# Adicione o caminho do projeto ao PATH do sistema
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simuladoapp.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_connection():
    """Função para testar a conexão SMTP e envio de email."""
    subject = 'Teste de Email - SimuladoApp'
    message = 'Este é um email de teste para verificar se a configuração SMTP está funcionando corretamente.'
    from_email = settings.EMAIL_HOST_USER
    recipient_list = ['luizgabriel3714@gmail.com']
    
    print(f"Tentando enviar email de {from_email} para {recipient_list[0]}...")
    print(f"Usando servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
    print(f"TLS ativado: {settings.EMAIL_USE_TLS}")
    
    try:
        result = send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        print(f"Email enviado com sucesso! Resultado: {result}")
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False

def print_email_settings():
    """Imprime as configurações de email atuais."""
    print("\n===== CONFIGURAÇÕES DE EMAIL =====")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER do settings: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD do settings: {settings.EMAIL_HOST_PASSWORD}")
    
    print("==================================\n")
    


if __name__ == "__main__":
    print_email_settings()
    test_email_connection()