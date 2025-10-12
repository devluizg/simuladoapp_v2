from django.urls import path
from . import views

urlpatterns = [
    # Rotas para Turmas
    path('', views.class_list, name='class_list'),
    path('create/', views.class_create, name='class_create'),
    path('<int:pk>/edit/', views.class_edit, name='class_edit'),
    path('<int:pk>/delete/', views.class_delete, name='class_delete'),
    path('class/<int:pk>/students/', views.class_students, name='class_students'),
    path('<int:pk>/add_students/', views.class_add_students, name='class_add_students'),
    path('<int:class_pk>/remove_student/<int:student_pk>/', views.class_remove_student, name='class_remove_student'),
    path('import-students/', views.import_students, name='import_students'),
    path('update-order/', views.update_class_order, name='update_class_order'),

    # Rotas para Estudantes
    path('student/form/', views.student_form, name='student_form'),
    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('student/<int:student_id>/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student-select-dashboard/', views.student_select_dashboard, name='student_select_dashboard'),
    path('student/<int:student_id>/simulado/<int:simulado_id>/', views.student_simulado_detail, name='student_simulado_detail'),

    # Rotas para Simulados e Dashboards de Desempenho
    path('classes/<int:class_id>/desempenho/', views.class_select_simulado, name='class_select_simulado'),
    path('class/<int:class_id>/simulado/<int:simulado_id>/dashboard/', views.class_performance_dashboard, name='class_performance_dashboard'),
    path('classes/<int:class_id>/simulados/<int:simulado_id>/dashboard/charts/',
         views.generate_class_dashboard_charts,
         name='class_dashboard_charts'),
    path('classes/<int:class_id>/simulados/<int:simulado_id>/limpar/', views.class_simulado_limpar, name='class_simulado_limpar'),

    # Rotas para Resultados do App
    path('app-resultados/', views.app_resultados, name='app_resultados'),
    path('app-resultados/<int:resultado_id>/', views.app_resultado_detalhes, name='app_resultado_detalhes'),
    path('app-resultados/limpar/', views.app_resultados_limpar, name='app_resultados_limpar'),

    # Rotas para detalhes e redirecionamentos de resultados
    path('resultado-detalhes/<str:fonte>/<int:resultado_id>/', views.resultado_detalhes_redirect, name='resultado_detalhes'),
    path('resultados/<str:fonte>/<int:resultado_id>/', views.resultado_detalhes, name='resultado_detalhes'),
    path('class/<int:class_id>/simulado/<int:simulado_id>/relatorio-pdf/',
         views.exportar_dashboard_pdf,
         name='exportar_dashboard_pdf'),

]