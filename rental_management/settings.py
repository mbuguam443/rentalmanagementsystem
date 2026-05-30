import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-w+8p!5#lb%g0z#h03!#q%6-@6a6d8-ufy_&qbjl*h%#cj5ij+s')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rental_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'rental_management.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'core' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS') else []

# M-Pesa Daraja API
DARAJA_CONSUMER_KEY = os.environ.get('DARAJA_CONSUMER_KEY', '9Fhevbx7JPg35tGmjhkaYNaZAuU9uP6S')
DARAJA_CONSUMER_SECRET = os.environ.get('DARAJA_CONSUMER_SECRET', 'k5MCkJz8DEo7WZHT')
DARAJA_PASSKEY = os.environ.get('DARAJA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')
DARAJA_SHORTCODE = os.environ.get('DARAJA_SHORTCODE', '174379')
DARAJA_BASE_URL = os.environ.get('DARAJA_BASE_URL', 'https://sandbox.safaricom.co.ke')
DARAJA_CALLBACK_URL = os.environ.get('DARAJA_CALLBACK_URL', 'https://58e4-102-205-50-218.ngrok-free.app/mpesa/callback/')
DARAJA_C2B_SHORTCODE = os.environ.get('DARAJA_C2B_SHORTCODE', '600000')
DARAJA_C2B_RESPONSE_TYPE = os.environ.get('DARAJA_C2B_RESPONSE_TYPE', 'Completed')
DARAJA_C2B_CONFIRMATION_URL = os.environ.get('DARAJA_C2B_CONFIRMATION_URL', 'https://58e4-102-205-50-218.ngrok-free.app/api/c2b/confirmation/')
DARAJA_C2B_VALIDATION_URL = os.environ.get('DARAJA_C2B_VALIDATION_URL', 'https://58e4-102-205-50-218.ngrok-free.app/api/c2b/validation/')
