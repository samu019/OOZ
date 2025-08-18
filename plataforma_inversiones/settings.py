import os
from pathlib import Path
from django.contrib.messages import constants as messages

# ===============================
# RUTA BASE DEL PROYECTO
# ===============================
BASE_DIR = Path(__file__).resolve().parent.parent

# ===============================
# CONFIGURACIONES GENERALES
# ===============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SECRET_KEY = 'django-insecure-cambia-esta-clave-por-una-segura'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# ===============================
# APLICACIONES INSTALADAS
# ===============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # App principal
    'inversiones.apps.InversionesConfig',

    # Extras
    'widget_tweaks',  # Agregado para manejar widgets en formularios
    'django_cron',  # Agregado para cron jobs
]

# ===============================
# MIDDLEWARE
# ===============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ===============================
# URL Y WSGI
# ===============================
ROOT_URLCONF = 'plataforma_inversiones.urls'
WSGI_APPLICATION = 'plataforma_inversiones.wsgi.application'

# ===============================
# PLANTILLAS
# ===============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
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

# ===============================
# BASE DE DATOS
# ===============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ===============================
# VALIDADORES DE CONTRASEÑA
# ===============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===============================
# INTERNACIONALIZACIÓN
# ===============================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ===============================
# ARCHIVOS ESTÁTICOS Y MEDIA
# ===============================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static",]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ===============================
# USUARIO PERSONALIZADO
# ===============================
AUTH_USER_MODEL = 'inversiones.CustomUser'

# ===============================
# LOGIN / LOGOUT
# ===============================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# ===============================
# LOGGING
# ===============================
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {'handlers': ['console'], 'level': 'DEBUG'},
}

# ===============================
# TAGS DE MENSAJES
# ===============================
MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}

# ===============================
# BILLETERA INTERNA Y SISTEMA DE TRANSACCIONES
# ===============================

# Definir una moneda para los depósitos y retiros
CRYPTOCURRENCY = "USDT"  # Puedes cambiar esta moneda según lo que quieras usar en la billetera interna

# Configuraciones adicionales para billetera interna
BILLETERA_INTERNA = True  # Indicar que usarás la billetera interna

# URL para los webhooks internos de depósitos y retiros
DEPOSITO_CALLBACK_URL = "https://tu_dominio.com/deposito/webhook/"
RETIRO_CALLBACK_URL = "https://tu_dominio.com/retiro/webhook/"

# Configuración de la red para los pagos criptográficos
RED_CRIPTO = "TRC20"  # Ajusta según la red que decidas usar (TRC20, ERC20, etc.)
