from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='questions_dashboard'),

    # Questões
    path('questoes/', views.questao_list, name='questao_list'),
    path('questoes/nova/', views.questao_create, name='questao_create'),
    path('questoes/<int:pk>/editar/', views.questao_update, name='questao_update'),
    path('questoes/<int:pk>/excluir/', views.questao_delete, name='questao_delete'),

    # Simulados - URLs específicas PRIMEIRO
    path('simulados/', views.simulado_list, name='simulado_list'),
    path('simulados/arquivados/', views.archived_simulado_list, name='archived_simulado_list'),
    path('simulados/novo/', views.simulado_create, name='simulado_create'),

    # URLs de progresso - COLOCAR ANTES das URLs genéricas
    path('simulados/<int:pk>/progresso/', views.progresso_pdf, name='progresso_pdf'),
    path('simulados/<int:pk>/status/', views.status_progresso, name='status_progresso'),
    path('simulados/<int:pk>/gerar-pdf/', views.gerar_pdf_com_progresso, name='gerar_pdf'),
    path('simulados/<int:pk>/atualizar-ordem/', views.update_questoes_ordem, name='update_questoes_ordem'),

    # URLs genéricas dos simulados
    path('simulados/<int:pk>/', views.simulado_detail, name='simulado_detail'),
    path('simulados/<int:pk>/editar/', views.simulado_edit, name='simulado_edit'),
    path('simulados/<int:pk>/excluir/', views.simulado_delete, name='simulado_delete'),

    # URLs com padrão "simulado" (sem 's')
    path('simulado/<int:pk>/pdf/', views.gerar_pdf, name='simulado_pdf'),
    path('simulado/<int:pk>/pdf/confirmar/', views.confirm_regenerate, name='confirm_regenerate'),
    path('simulado/form/', views.simulado_form, name='simulado_form'),
    path('simulado/form/<int:pk>/', views.simulado_form, name='simulado_form_edit'),

    # URLs do sistema de gabaritos
    path('simulado/<int:pk>/gabaritos/', views.simulado_gabaritos_historico, name='simulado_gabaritos_historico'),
    path('simulado/<int:pk>/gabaritos/<uuid:versao_id>/', views.visualizar_gabarito_versao, name='visualizar_gabarito_versao'),
    path('simulado/<int:pk>/gabaritos/comparar/', views.comparar_versoes_gabarito, name='comparar_versoes_gabarito'),
    path('simulado/<int:pk>/gabaritos/definir-oficial/', views.definir_gabarito_oficial, name='definir_gabarito_oficial'),
    path('simulado/<int:pk>/gabaritos/<uuid:versao_id>/excluir/', views.excluir_versao_gabarito, name='excluir_versao_gabarito'),

    # Outras URLs
    path('adicionar-questao-simulado/', views.adicionar_questao_simulado, name='adicionar_questao_simulado'),
    path('download/<str:key>/', views.download_temp_file, name='download_temp_file'),
]