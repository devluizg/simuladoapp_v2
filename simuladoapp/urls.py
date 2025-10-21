from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView  # <- IMPORTANTE
from rest_framework.authtoken.views import obtain_auth_token
from classes.views import update_simulado_area
from .views import privacy_policy  # Importa a nova view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Sitemap.xml estático
    path("sitemap.xml", TemplateView.as_view(
        template_name="sitemap.xml",
        content_type="application/xml"
    ), name="sitemap"),

    path('accounts/', include('accounts.urls')),
    path('api/', include('api.urls')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('', include('questions.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('classes/', include('classes.urls')),
    path('update_simulado_area/', update_simulado_area, name='update_simulado_area'),
    path('privacy-policy/', privacy_policy, name='privacy_policy'),
    path('payments/', include('payments.urls', namespace='payments')),
]

# Servir arquivos de mídia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
