import os
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1', 'localhost'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Railway / proxy HTTPS
if env.bool('BEHIND_PROXY', default=False):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'budgeting.apps.BudgetingConfig',
    'accounts.apps.AccountsConfig',
    'sitepages.apps.SitepagesConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.LastActivityMiddleware',
]

if DEBUG:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(
        MIDDLEWARE.index('django.middleware.clickjacking.XFrameOptionsMiddleware') + 1,
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

ROOT_URLCONF = 'budget_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'budget_project.wsgi.application'

# Local .env uses DB_*; Railway/Render may use MYSQL*. Aiven needs DB_SSL=True.
_db_options = {
    'charset': 'utf8mb4',
    'init_command': (
        "SET sql_mode='STRICT_TRANS_TABLES', "
        "NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'"
    ),
}
if env.bool('DB_SSL', default=False):
    # Aiven MySQL: ssl-mode=REQUIRED (certificate verify optional for free tier).
    _db_options['ssl'] = {'ssl': True}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQLDATABASE') or env('DB_NAME'),
        'USER': os.environ.get('MYSQLUSER') or env('DB_USER'),
        'PASSWORD': os.environ.get('MYSQLPASSWORD') or env('DB_PASSWORD'),
        'HOST': os.environ.get('MYSQLHOST') or env('DB_HOST', default='127.0.0.1'),
        'PORT': os.environ.get('MYSQLPORT') or env('DB_PORT', default='3306'),
        'OPTIONS': _db_options,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uk'
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'budgeting:dashboard'
LOGOUT_REDIRECT_URL = 'budgeting:home'

INTERNAL_IPS = ['127.0.0.1']

from django.contrib.messages import constants as message_constants

MESSAGE_TAGS = {
    message_constants.ERROR: 'danger',
}

# Листи зберігаються у файли (локальна розробка). У DEBUG посилання
# також показується на сторінці після скидання пароля.
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
DEFAULT_FROM_EMAIL = 'noreply@financehelper.local'
EMAIL_SUBJECT_PREFIX = '[Finance Helper] '
