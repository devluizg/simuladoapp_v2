#accounts/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .forms import CustomUserCreationForm
import uuid
from django.contrib.auth.forms import SetPasswordForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.sites.shortcuts import get_current_site

User = get_user_model()

def generate_unique_username(first_name):
    """Gera um username único baseado no primeiro nome."""
    username = first_name.lower()
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{first_name.lower()}{counter}"
        counter += 1
    return username

def register(request):
    """
    View para registro de novos usuários.
    """
    if request.method == 'POST':
        # Verifica se é uma solicitação de reenvio de email
        if 'resend_email' in request.POST:
            return resend_activation_email(request)
        
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.activation_token = str(uuid.uuid4())
            user.activation_token_expiry = timezone.now() + timedelta(days=1)
            user.is_active = False
            
            # Primeiro salva o usuário para que envio de email não falhe com usuário inexistente
            user.save()
            
            # Agora envia o email de ativação
            if send_activation_email(request, user):
                # Se for uma requisição AJAX, retorna resposta JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Cadastro realizado com sucesso! Verifique seu email para ativar sua conta.'
                    })
                
                # Se não for AJAX, redireciona para a página de login com mensagem
                messages.success(request, 'Cadastro realizado com sucesso! Verifique seu email para ativar sua conta.')
                return redirect('accounts:login')
            else:
                # Se houver erro no envio do email
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Erro ao enviar email de ativação. Por favor, tente novamente mais tarde.'
                    })
                
                messages.error(request, 'Erro ao enviar email de ativação. Por favor, tente novamente mais tarde.')
        else:
            # Se o formulário for inválido e for uma requisição AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(error) for error in error_list]
                
                return JsonResponse({
                    'success': False,
                    'message': 'Erro ao processar o formulário. Verifique os campos e tente novamente.',
                    'errors': errors
                })
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def activate_account(request, token):
    try:
        user = User.objects.get(activation_token=token, is_active=False)
        
        # Verifica se o token não expirou
        if timezone.now() < user.activation_token_expiry:
            # Ativa a conta e marca o email como verificado
            user.is_active = True
            user.email_verified = True
            
            # Substitui o token por um UUID válido que indica "token usado"
            user.activation_token = uuid.UUID('00000000-0000-0000-0000-000000000000')
            user.save()
            
            messages.success(request, 'Sua conta foi ativada com sucesso! Agora você pode fazer login.')
            return render(request, 'accounts/activation_success.html')
        else:
            messages.error(request, 'O link de ativação expirou. Por favor, solicite um novo link de ativação.')
            return render(request, 'accounts/activation_failed.html', {'email': user.email})
    except User.DoesNotExist:
        messages.error(
            request,
            'O link de ativação é inválido ou já foi usado. Por favor, tente se registrar novamente.'
        )
        return render(request, 'accounts/activation_failed.html')


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            # Pegando o site atual
            current_site = get_current_site(request)
            domain = current_site.domain
            protocol = 'https' if request.is_secure() else 'http'

            # Renderiza o template do e-mail
            html_message = render_to_string('accounts/password_reset_email.html', {
                'user': user,
                'domain': domain,
                'protocol': protocol,
                'uid': uid,
                'token': token,
            })

            # Envia o e-mail
            send_mail(
                'Redefinição de Senha',
                strip_tags(html_message),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            messages.success(
                request,
                'Email enviado! Verifique sua caixa de entrada para redefinir sua senha.'
            )
            return redirect('accounts:password_reset_done')

        except User.DoesNotExist:
            messages.error(
                request,
                'Não encontramos uma conta com este email. Verifique se digitou corretamente.'
            )
    
    return render(request, 'accounts/password_reset.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Sua senha foi redefinida com sucesso!')
                return redirect('accounts:password_reset_complete')
        else:
            form = SetPasswordForm(user)
        return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        messages.error(request, 'O link de redefinição de senha é inválido ou expirou.')
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})

def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')

def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')

def send_activation_email(request, user):
    """
    Função auxiliar para enviar o email de ativação.
    """
    # Construa o link de ativação completo
    activation_link = request.build_absolute_uri(
        reverse('accounts:activate', kwargs={'token': user.activation_token})
    )
    
    # Contexto para o template do email
    context = {
        'user': user,
        'activation_link': activation_link,
        'expiry_days': 1  # Dias até a expiração do token
    }
    
    # Renderiza o conteúdo do email
    subject = 'Ative sua conta na SimuladoApp'
    try:
        # Usar diretamente o template existente
        html_message = render_to_string('accounts/activation_email.html', context)
        plain_message = strip_tags(html_message)
        
        # Envia o email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

def resend_activation_email(request):
    """
    View para reenviar o email de ativação.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Verifica se o usuário já está ativo
            if user.is_active:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Esta conta já está ativa. Por favor, faça login.'
                    })
                messages.info(request, 'Esta conta já está ativa. Por favor, faça login.')
                return redirect('accounts:login')
            
            # Gera novo token e atualiza data de expiração
            user.activation_token = str(uuid.uuid4())
            user.activation_token_expiry = timezone.now() + timedelta(days=1)
            user.save()
            
            # Envia o email de ativação
            if send_activation_email(request, user):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Um novo email de ativação foi enviado. Por favor, verifique sua caixa de entrada.'
                    })
                messages.success(request, 'Um novo email de ativação foi enviado. Por favor, verifique sua caixa de entrada.')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Ocorreu um erro ao enviar o email. Por favor, tente novamente mais tarde.'
                    })
                messages.error(request, 'Ocorreu um erro ao enviar o email. Por favor, tente novamente mais tarde.')
                
        except User.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Email não encontrado no sistema.'
                })
            messages.error(request, 'Email não encontrado no sistema.')
        
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Método não permitido.'
        })
        
    return redirect('accounts:login')

@login_required
def profile_update(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('accounts:dashboard')
        
    return redirect('accounts:dashboard')