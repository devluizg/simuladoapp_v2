from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    ClassViewSet, StudentViewSet, QuestaoViewSet, SimuladoViewSet,
    test_connection, user_info, app_config, procesar_cartao_resposta,
    submit_resultado, debug_token_request, aluno_login,
    list_all_classes, list_class_students, list_class_simulados,
    get_detalhes_resultado  # ✅ ADICIONAR ESTA IMPORTAÇÃO
)

router = DefaultRouter()
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'questoes', QuestaoViewSet, basename='questao')
router.register(r'simulados', SimuladoViewSet, basename='simulado')

urlpatterns = [
    # Rotas do router
    path('', include(router.urls)),

    # Autenticação
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('aluno/login/', aluno_login, name='aluno_login'),

    # Utilitários
    path('test-connection/', test_connection, name='test_connection'),
    path('user-info/', user_info, name='user_info'),
    path('app-config/', app_config, name='app_config'),
    path('debug-token/', debug_token_request, name='debug_token_request'),

    # Cartão de resposta e resultados
    path('procesar-cartao/', procesar_cartao_resposta, name='procesar_cartao_resposta'),
    path('resultados/submit/', submit_resultado, name='submit_resultado'),

    # ✅ NOVA ROTA: Detalhes completos de um resultado
    path('resultados/<int:resultado_id>/detalhes/',
         get_detalhes_resultado,
         name='get_detalhes_resultado'),

    # Rotas auxiliares para listagem
    path('classes/list/', list_all_classes, name='list_all_classes'),
    path('classes/<int:class_id>/students/', list_class_students, name='list_class_students'),
    path('classes/<int:class_id>/simulados/', list_class_simulados, name='list_class_simulados'),

    path('subscription-status/', views.subscription_status, name='subscription_status'), 
]