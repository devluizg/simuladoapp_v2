from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (  # Importe da própria view, não de accounts.views
    ClassViewSet, StudentViewSet, QuestaoViewSet, SimuladoViewSet,
    test_connection, user_info, app_config, procesar_cartao_resposta,
    submit_resultado,  # Adicione esta importação
    debug_token_request
)

router = DefaultRouter()
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'students', StudentViewSet, basename='student')
router.register(r'questoes', QuestaoViewSet)
router.register(r'simulados', SimuladoViewSet, basename='simulado')

urlpatterns = [
    # Incluir as rotas do router sem adicionar o prefixo 'api/' novamente
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('test-connection/', test_connection, name='test_connection'),
    path('user-info/', user_info, name='user_info'),
    path('app-config/', app_config, name='app_config'),
    path('procesar-cartao/', procesar_cartao_resposta, name='procesar_cartao_resposta'),
    path('debug-token/', debug_token_request,  name='debug_token_request'),
    path('resultados/submit/', submit_resultado, name='submit_resultado'),  # Alterado de views.submit_resultado para apenas submit_resultado
]