# settings.py
from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv
from decouple import config

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o .env manualmente
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

# ========================================
# CONFIGURAÇÕES BÁSICAS
# ========================================

SECRET_KEY = config('SECRET_KEY', default='sua-chave-secreta-altere-em-producao')

DEBUG = config('DEBUG', default=False, cast=bool)

<<<<<<< HEAD
<<<<<<< Updated upstream
# Alterar para incluir explicitamente o domínio PythonAnywhere
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'simuladoapp.com.br', 'www.simuladoapp.com.br']
=======
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1',
    '10.0.2.2',  # Para Android Emulator
    '192.168.1.10',  # ⬅️ SEU IP
    'simuladoapp.com.br', 
    'www.simuladoapp.com.br',
    '.pythonanywhere.com',
    'lauric-nonparticipating-rhys.ngrok-free.dev',
=======
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    'simuladoapp.com.br', 
    'www.simuladoapp.com.br',
    '.pythonanywhere.com',  # Para desenvolvimento no PythonAnywhere
    'lauric-nonparticipating-rhys.ngrok-free.dev', # Para webhooks do Stripe via ngrok
>>>>>>> pagamentos_paginas
]

# ========================================
# SEGURANÇA
# ========================================
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> pagamentos_paginas

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    # SECURE_SSL_REDIRECT = True  # Descomente em produção
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ========================================
# APLICATIVOS INSTALADOS
# ========================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps do projeto
    'accounts',
    'questions',
    'classes',
    'api',
<<<<<<< Updated upstream
    'creditos',
<<<<<<< HEAD
=======
    'payments',  # Sistema de pagamentos
    
    # Apps de terceiros
>>>>>>> Stashed changes
=======
    'payments',  # Sistema de pagamentos
    
    # Apps de terceiros
>>>>>>> pagamentos_paginas
    'ckeditor',
    'ckeditor_uploader',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'widget_tweaks',
    'whitenoise.runserver_nostatic',
]

SITE_ID = 1

# ========================================
# MIDDLEWARE
# ========================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Arquivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Middlewares customizados
    'accounts.middleware.RedirectIfLoggedInMiddleware',
    
    # ===== MIDDLEWARES DO SISTEMA DE PAGAMENTOS =====
    'payments.middleware.SubscriptionMiddleware',  # Adiciona subscription ao request
    'payments.middleware.SubscriptionWarningMiddleware',  # Avisos automáticos
    # 'payments.middleware.SubscriptionAccessMiddleware',  # Descomente para bloqueio automático
    'payments.middleware.SubscriptionCacheMiddleware',  # Gerenciamento de cache
]

# ========================================
# CONFIGURAÇÕES DE URL E WSGI
# ========================================

ROOT_URLCONF = 'simuladoapp.urls'
WSGI_APPLICATION = 'simuladoapp.wsgi.application'

# ========================================
# TEMPLATES
# ========================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                
                # ===== CONTEXT PROCESSORS DO PAYMENTS =====
                'payments.context_processors.subscription_context',
                'payments.context_processors.subscription_features',
            ],
        },
    },
]

# ========================================
# BANCO DE DADOS
# ========================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ========================================
# VALIDAÇÃO DE SENHAS
# ========================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]

# ========================================
# INTERNACIONALIZAÇÃO
# ========================================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Formato de data e hora
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'

# ========================================
# ARQUIVOS ESTÁTICOS E MÍDIA
# ========================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Criar diretórios necessários
TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(MEDIA_ROOT, exist_ok=True)

# ========================================
# AUTENTICAÇÃO
# ========================================

AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================================
# CONFIGURAÇÕES DE EMAIL
# ========================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='simuladoapp@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='gswkljrybtjxaxxt')
DEFAULT_FROM_EMAIL = 'SimuladoApp <simuladoapp@gmail.com>'
EMAIL_TIMEOUT = 20
DEFAULT_CHARSET = 'utf-8'

# ========================================
# STRIPE - SISTEMA DE PAGAMENTOS
# ========================================

# Chaves do Stripe (obtenha em https://dashboard.stripe.com/apikeys)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

print("="*60)
print(f"DEBUG SETTINGS: A chave pública do Stripe é: '{STRIPE_PUBLIC_KEY}'")
print("="*60)


# Configurações adicionais do Stripe
STRIPE_LIVE_MODE = not DEBUG  # False em desenvolvimento, True em produção

# URLs de redirecionamento (ajuste conforme seu domínio)
STRIPE_SUCCESS_URL = config('STRIPE_SUCCESS_URL', default='http://localhost:8000/payments/checkout/success/')
STRIPE_CANCEL_URL = config('STRIPE_CANCEL_URL', default='http://localhost:8000/payments/checkout/cancel/')

# ========================================
# CACHE
# ========================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
    'subscription_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'subscription-cache',
        'TIMEOUT': 300,  # 5 minutos
    },
    'pdf_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'pdf-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 50,
        }
    }
}

# ========================================
# REST FRAMEWORK E JWT
# ========================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# ========================================
# CORS
# ========================================

CORS_ALLOW_ALL_ORIGINS = DEBUG  # True apenas em desenvolvimento

if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        'https://simuladoapp.com.br',
        'https://www.simuladoapp.com.br',
    ]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["DELETE", "GET", "OPTIONS", "PATCH", "POST", "PUT"]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# ========================================
# LOGGING
# ========================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
        'payments_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'payments.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'payments': {
            'handlers': ['console', 'payments_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'stripe': {
            'handlers': ['console', 'payments_file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# ========================================
# CKEDITOR
# ========================================

CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent'],
            ['Image', 'Table'],
            ['Link', 'Unlink'],
            ['RemoveFormat'],
            ['MathType', 'ChemType'],
        ],
        'autoGrow_onStartup': True,
        'autoGrow_minHeight': 300,
        'autoGrow_maxHeight': 500,
        'autoGrow_bottomSpace': 10,
        'width': '100%',
        'extraPlugins': ','.join([
            'uploadimage', 'div', 'autolink', 'autoembed', 'embedsemantic',
            'autogrow', 'widget', 'lineutils', 'clipboard', 'dialog',
            'dialogui', 'elementspath', 'mathjax', 'pastetools'
        ]),
        'mathJaxLib': '//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-AMS_HTML',
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,
        'forcePasteAsPlainText': False,
        'pasteFromWordRemoveFontStyles': True,
        'pasteFromWordRemoveStyles': True,
        'pasteFilter': 'p; strong; em; u; ol; ul; li; img[!src,alt,width,height]; table; tr; td; th',
    },
    'alternativas': {
        'toolbar': 'Alternativas',
        'toolbar_Alternativas': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Image', 'MathType', 'ChemType'],
        ],
        'height': '40px',
        'autoGrow_minHeight': 40,
        'autoGrow_maxHeight': 200,
        'autoGrow_bottomSpace': 5,
        'autoGrow_onStartup': True,
        'removePlugins': 'resize',
        'extraPlugins': 'autogrow,pastetools',
        'width': '100%',
        'forcePasteAsPlainText': False,
        'pasteFromWordRemoveFontStyles': True,
        'pasteFromWordRemoveStyles': True,
        'pasteFilter': 'p; strong; em; u; ol; ul; li; img[!src,alt,width,height]',
    }
}

# ========================================
# CONFIGURAÇÕES DE PDF
# ========================================

PDF_GENERATION_SETTINGS = {
    'MAX_WORKERS': 2,
    'TIMEOUT_PER_VERSION': 60,
    'TOTAL_TIMEOUT': 300,
    'ENABLE_IMAGE_OPTIMIZATION': True,
    'ENABLE_HTML_MINIFICATION': True,
}

# ========================================
# CONFIGURAÇÕES DA APLICAÇÃO
# ========================================

SIMULADO_MAX_QUESTOES = 45
ALLOWED_QUESTION_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_QUESTION_IMAGE_SIZE = 5242880  # 5MB

# ========================================
# MENSAGENS
# ========================================

from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

# ========================================
# SESSÕES
# ========================================

SESSION_COOKIE_AGE = 1209600  # 2 semanas
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SESSION_COOKIE_SECURE = True

# ========================================
# CSRF
# ========================================

CSRF_COOKIE_HTTPONLY = False  # Para permitir acesso via JavaScript se necessário
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

if not DEBUG:
    CSRF_COOKIE_SECURE = True