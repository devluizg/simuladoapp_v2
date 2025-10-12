from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import EmailAuthenticationForm
from .forms import CustomPasswordResetForm

app_name = 'accounts'  

urlpatterns = [
    path('register/', views.register, name='register'),
    path('activate/<uuid:token>/', views.activate_account, name='activate'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=EmailAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('resend-activation/', views.resend_activation_email, name='resend_activation'),  
    path('profile/update/', views.profile_update, name='profile_update'),

    # Redefinição de senha
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.txt',  # Plain text version
        subject_template_name='accounts/password_reset_subject.txt',
        html_email_template_name='accounts/password_reset_email.html',  # HTML version
        form_class=CustomPasswordResetForm,  # Add this line
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]
