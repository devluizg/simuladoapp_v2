from django.shortcuts import render

def privacy_policy(request):
    """
    Renderiza a página de Política de Privacidade.
    """
    return render(request, 'privacy_policy.html')
