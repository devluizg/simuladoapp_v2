from django.urls import path
from . import views

app_name = 'creditos'

urlpatterns = [
    # ✅ AJUSTADO: Remover o prefixo 'api/creditos/' pois já vem do urls.py principal
    path('api/creditos/', views.consultar_creditos, name='consultar_creditos'),  # /api/creditos/
    path('api/creditos/history/', views.get_credit_history, name='credit_history'),  # /api/creditos/history/
    path('api/usar_credito/', views.usar_credito, name='usar_credito'),  # /api/usar_credito/
    path('api/credits/plans/', views.get_available_plans, name='credit_plans'),  # /api/credits/plans/
    path('api/creditos/comprar/', views.comprar_creditos, name='comprar_creditos'),  # /api/creditos/comprar/

    # Opcional: rota para visualização web
    path('pagina/', views.pagina_creditos, name='pagina_creditos'),  # /api/creditos/pagina/
]