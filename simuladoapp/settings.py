from pathlib import Path
import os
from datetime import timedelta

from dotenv import load_dotenv
from decouple import config

# Diretório base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o .env manualmente
load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))

# Configurações Básicas
SECRET_KEY = config('SECRET_KEY', default='sua-chave-secreta')

DEBUG = config('DEBUG', default=False, cast=bool)

# Alterar para incluir explicitamente o domínio PythonAnywhere
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'simuladoapp.com.br', 'www.simuladoapp.com.br']

# SECURE_SETTINGS para produção
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    # Comentar temporariamente para testes
    # SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 ano
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'same-origin'

# Aplicativos Instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'questions',
    'classes',
    'api',
    'creditos',
    'ckeditor',
    'ckeditor_uploader',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',    # Para CORS
    'django_filters',
    'widget_tweaks',
    'whitenoise.runserver_nostatic',  # Adicionar para arquivos estáticos
]

SITE_ID = 1

# Configurações de Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Adicionar para servir arquivos estáticos
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.RedirectIfLoggedInMiddleware',
]

# Configuração de Compressão para arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

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

# Configurações CORS - adicionar suporte a aplicativos móveis
CORS_ALLOW_ALL_ORIGINS = True  # Para testes iniciais

# Quando estiver pronto para produção, troque para:
# CORS_ALLOWED_ORIGINS = [
#     'https://devluizg.pythonanywhere.com',
#     'http://localhost:3000',
#     'capacitor://localhost',  # Para apps híbridos
#     'app://simuladoapp'  # Para seu app nativo
# ]

# Configurações importantes para permitir autenticação
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

# Configuração da URL raiz
ROOT_URLCONF = 'simuladoapp.urls'

# Configurações de Templates
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
            ],
        },
    },
]

# Configuração WSGI
WSGI_APPLICATION = 'simuladoapp.wsgi.application'

# Configurações do Banco de Dados
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
            'ssl': {},  # Remover se causar problemas
        },
    }
}

# Validação de Senhas
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

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configurações de Mídia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Criar diretório para arquivos temporários se não existir
TEMP_DIR = os.path.join(MEDIA_ROOT, 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

# Tipo de campo de chave primária padrão
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações de Autenticação Personalizada
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Backends de Autenticação
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Configurações de Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'simuladoapp@gmail.com'
EMAIL_HOST_PASSWORD = 'gswkljrybtjxaxxt'
DEFAULT_FROM_EMAIL = 'SimuladoApp <simuladoapp@gmail.com>'
EMAIL_TIMEOUT = 20
DEFAULT_CHARSET = 'utf-8'

# JWT Settings
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

# Configurações de Segurança Adicionais
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Configurações de cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configurações do CKEditor
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
            'uploadimage',
            'div',
            'autolink',
            'autoembed',
            'embedsemantic',
            'autogrow',
            'widget',
            'lineutils',
            'clipboard',
            'dialog',
            'dialogui',
            'elementspath',
            'mathjax',
            'pastetools'
        ]),
        'mathJaxLib': '//cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-AMS_HTML',
        'removePlugins': 'stylesheetparser',
        'allowedContent': True,
        # Configurações adicionadas para melhorar a limpeza de formatação
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
        # Configurações adicionadas para melhorar a limpeza de formatação
        'forcePasteAsPlainText': False,
        'pasteFromWordRemoveFontStyles': True,
        'pasteFromWordRemoveStyles': True,
        'pasteFilter': 'p; strong; em; u; ol; ul; li; img[!src,alt,width,height]',
    }
}

# Cache para templates de PDF
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'pdf-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 50,
        }
    }
}

PDF_GENERATION_SETTINGS = {
    'MAX_WORKERS': 2,  # Reduzir workers
    'TIMEOUT_PER_VERSION': 60,  # Timeout por versão
    'TOTAL_TIMEOUT': 300,  # Timeout total
    'ENABLE_IMAGE_OPTIMIZATION': True,
    'ENABLE_HTML_MINIFICATION': True,
}

# Configurações de aplicação
SIMULADO_MAX_QUESTOES = 45
ALLOWED_QUESTION_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
MAX_QUESTION_IMAGE_SIZE = 5242880  # 5MB