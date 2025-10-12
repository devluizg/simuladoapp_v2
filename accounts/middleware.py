from django.shortcuts import redirect
from django.urls import reverse

class RedirectIfLoggedInMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Redireciona usuários autenticados que tentam acessar a página de login para o dashboard.
        """
        # Verifica se o usuário está autenticado e acessando a página de login
        if request.user.is_authenticated and request.path == reverse('accounts:login'):
            return redirect('accounts:dashboard')

        response = self.get_response(request)
        return response
