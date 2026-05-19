"""Django settings for my-blog (production-grade)."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _split_csv(name: str):
    raw = os.environ.get(name, '')
    return [p.strip() for p in raw.split(',') if p.strip()]


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {'1', 'true', 'yes', 'on'}


DEBUG = _bool_env('DJANGO_DEBUG', True)

# SECURITY: never expose a real key in the repo. The placeholder is *only* used
# for local dev; production will refuse to start without DJANGO_SECRET_KEY.
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-only-not-for-production-replace-me-with-os-environ-set-key',
)

if not DEBUG:
    if not SECRET_KEY or SECRET_KEY.startswith(('dev-only', 'django-insecure')):
        raise ValueError(
            'DJANGO_SECRET_KEY must be set to a strong secret when DJANGO_DEBUG=False.'
        )

hosts = _split_csv('DJANGO_ALLOWED_HOSTS')
if hosts:
    ALLOWED_HOSTS = hosts
elif DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
else:
    raise ValueError('DJANGO_ALLOWED_HOSTS must be set when DJANGO_DEBUG=False.')

# Internal IPs (for debug toolbar, etc.)
INTERNAL_IPS = ['127.0.0.1']

# Customisable admin path; default `admin/` but recommend changing in prod.
ADMIN_URL = os.environ.get('DJANGO_ADMIN_URL', 'admin/').lstrip('/')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.syndication',
    'blog.apps.BlogConfig',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves staticfiles efficiently when nginx is unavailable.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'blog.middleware.LanguageCookieMiddleware',
]

ROOT_URLCONF = 'config.urls'

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
                'dashboard.context_processors.dashboard_counts',
                'blog.context_processors.site_settings',
                'blog.context_processors.user_lang',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DJANGO_DB_NAME', 'fazliddin_blog'),
        'USER': os.environ.get('DJANGO_DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DJANGO_DB_HOST', 'localhost'),
        'PORT': os.environ.get('DJANGO_DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.environ.get('DJANGO_DB_CONN_MAX_AGE', '60')),
        'CONN_HEALTH_CHECKS': True,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
LANGUAGES = [('en', 'English'), ('uz', 'Uzbek')]
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django 5.0+ replaced ``STATICFILES_STORAGE`` with the ``STORAGES`` mapping.
# Production uses WhiteNoise's manifest storage so deploys auto-bust browser
# caches (``style.css`` -> ``style.<hash>.css``); without this the 7-day Nginx
# cache means users see stale CSS/JS for a week after every deploy.
_STATIC_BACKEND = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
    if not DEBUG
    else 'django.contrib.staticfiles.storage.StaticFilesStorage'
)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': _STATIC_BACKEND},
}
# Tolerate references in templates to files that no longer exist (mostly
# admin assets) instead of crashing the whole page during ``collectstatic``.
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_MAX_AGE = 60 * 60 * 24 * 365  # hashed assets are immutable

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# File upload limits (5MB images by default).
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('DJANGO_MAX_UPLOAD', str(5 * 1024 * 1024)))
FILE_UPLOAD_MAX_MEMORY_SIZE = DATA_UPLOAD_MAX_MEMORY_SIZE
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# CSRF.
csrf_list = _split_csv('DJANGO_CSRF_TRUSTED_ORIGINS')
if csrf_list:
    CSRF_TRUSTED_ORIGINS = csrf_list
elif DEBUG:
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
else:
    raise ValueError('DJANGO_CSRF_TRUSTED_ORIGINS must be set when DJANGO_DEBUG=False.')

# Auth.
LOGIN_URL = '/dashboard/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days

# ---- Production hardening (HTTPS) ----
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', str(60 * 60 * 24 * 30)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _bool_env('DJANGO_HSTS_INCLUDE_SUBDOMAINS', False)
    SECURE_HSTS_PRELOAD = _bool_env('DJANGO_HSTS_PRELOAD', False)

# Email.
EMAIL_BACKEND = os.environ.get(
    'DJANGO_EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = _bool_env('DJANGO_EMAIL_USE_TLS', True)
EMAIL_TIMEOUT = int(os.environ.get('DJANGO_EMAIL_TIMEOUT', '15'))
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'hello@fazliddin.com')
SERVER_EMAIL = os.environ.get('DJANGO_SERVER_EMAIL', DEFAULT_FROM_EMAIL)
CONTACT_NOTIFY_EMAIL = os.environ.get('DJANGO_CONTACT_NOTIFY_EMAIL', '')
SITE_DEFAULT_OG_IMAGE = os.environ.get('DJANGO_DEFAULT_OG_IMAGE', '/static/images/og-default.svg')

# Caching: per-site (URL+cookie aware).
CACHES = {
    'default': {
        'BACKEND': os.environ.get(
            'DJANGO_CACHE_BACKEND',
            'django.core.cache.backends.locmem.LocMemCache',
        ),
        'LOCATION': os.environ.get('DJANGO_CACHE_LOCATION', 'my-blog-cache'),
    }
}

# Logging — print app errors with traceback even in production gunicorn logs.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {'format': '[{levelname}] {asctime} {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django.request': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'blog': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'dashboard': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}

# Rate-limiting (per-IP, soft, in-cache). Customisable via env.
RATELIMIT_SUBSCRIBE = int(os.environ.get('DJANGO_RATELIMIT_SUBSCRIBE', '5'))   # /min
RATELIMIT_CONTACT = int(os.environ.get('DJANGO_RATELIMIT_CONTACT', '3'))       # /min
RATELIMIT_LOGIN = int(os.environ.get('DJANGO_RATELIMIT_LOGIN', '10'))          # /min
