"""
Django settings for the FineStor project.

Created with Django 5.1.7. Using django-tables2, 
django-celery-beat, django-crispy-forms, 
django-redis-server, and bootstrap5.
"""

from pathlib import Path
import os
import sys
import re
import logging

# Helper Functions
#########################################################################################################
# Helper function to extract the last version number from the README file.
def get_last_version_from_readme():
    if not os.path.exists("README.MD"):
        return "1.?.?"
    try:
        with open("README.MD", "r", encoding="utf-8") as f:
            content = f.read()
            # Use regex to find all version numbers prefixed by 'v'
            versions = re.findall(r'v(\d+\.\d+\.\d+)', content)
            return versions[-1] if versions else "Unknown"
    except Exception as e:
        return f"Error: {str(e)}"

# Helper function to read a secret from Docker secrets or an environment variable.
def get_secret(secret_name, env_var):
    """Try to read a secret from Docker secrets, then fall back to an environment variable."""
    try:
        with open(f'/run/secrets/{secret_name}', 'r') as f:
            return f.read().strip()
    except IOError:
        return os.getenv(env_var)

# Link error messages to Bootstrap danger class
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}


# Fundemental settings
#########################################################################################################
# Reconfigures the standard output (stdout) encoding to UTF-8 to support non-ASCII characters.
sys.stdout.reconfigure(encoding='utf-8')

# The BASE_DIR is the absolute path to the project directory, used to help generate file paths relative to the project.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# the URL prefix for the application. This is typically the base URL where the application is hosted.
BASE_URL = os.getenv("BASE_URL")

# Specifies the URL configuration module for the project.
# This is typically the file where all URL patterns for the project are defined.
ROOT_URLCONF = 'main.urls'

# Specifies the custom user model to be used in place of the default Django User model.
# Here, 'users.CustomUser' refers to a user model defined in the 'users' app with the name 'CustomUser'.
AUTH_USER_MODEL = 'users.CustomUser'

# Specifies the WSGI application used to serve the Django project.
# This is typically set to the path to your WSGI application file in the main app.
WSGI_APPLICATION = 'main.wsgi.application'

# Defines where the user should be redirected after successfully logging in.
LOGIN_REDIRECT_URL = '/'

# # Specifies the URL to redirect to for the login page.
LOGIN_URL = '/manage/login/'

# Defines the URL where the user will be redirected after logging out.
LOGOUT_REDIRECT_URL = 'index'

# Read the secret key from Docker secrets or environment variable.
SECRET_KEY = get_secret('DJANGO_SECRET_KEY', 'DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG should be set to False in production to prevent sensitive data exposure in errors.
DEBUG = os.environ.get('DEBUG_STATUS') == 'True'

# Production settings
#########################################################################################################
# CORS, CSRF, and Session settings for Cross-Origin Resource Sharing.
# CORS, CSRF, and Session settings for Cross-Origin Resource Sharing.
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    SESSION_COOKIE_DOMAIN = None
    CSRF_COOKIE_DOMAIN = None
    CSRF_TRUSTED_ORIGINS = [BASE_URL, 'http://localhost:8000']
    logging.basicConfig(level=logging.DEBUG)
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [BASE_URL]
    SESSION_COOKIE_DOMAIN = BASE_URL.replace("https://", "").replace("http://", "")
    CSRF_COOKIE_DOMAIN = BASE_URL.replace("https://", "").replace("http://", "")
    CSRF_TRUSTED_ORIGINS = [BASE_URL]
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# SECURITY WARNING: don't allow all hosts in production!
# List of allowed host/domain names that the app can serve.
# In production, this should only include trusted domain names.
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Control whether the site can be embedded in an <iframe> externally.
# Prevents the site from being embedded in an iframe on other websites for security reasons.
X_FRAME_OPTIONS = "SAMEORIGIN"

# Silences specific system checks during Django startup.
# This is often used to suppress warnings you consider non-critical or specific to your environment.
SILENCED_SYSTEM_CHECKS = ["security.W019"]


# Application settings
#########################################################################################################
# Installed applications are the Django apps and third-party packages that are used in the project.
INSTALLED_APPS = [
    'users',
    'core',
    'storage',
    'treasury',
    'salary',
    'finance',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    "crispy_bootstrap5",
    'django_tables2',
    'debug_toolbar',
    'report_builder',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'csp.middleware.CSPMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# For Docker/containers, you might need:
# import socket
# hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
# INTERNAL_IPS = [ip[:-1] + '1' for ip in ips] + ['127.0.0.1']

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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
# PostgreSQL database settings.
# Defines the database settings, including the database engine and connection parameters.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': get_secret('POSTGRES_PASSWORD', 'POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST', 'db'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Redis Cache configuration for the Django app, usually for storing temporary data for better performance.
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL_DB', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 20,
            'CONNECTION_POOL_KWARGS': {"max_connections": 50},

        }
    }
}

# Password validation settings to enhance security for user passwords.
# These settings control the password complexity and validation checks.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Session and CSRF settings
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Celery configuration for task queue management.
# This includes settings for the broker, which in this case is Redis.
# CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/2')
# CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/3')
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'

# Allows crispy-forms to use the 'bootstrap5' template pack for rendering form fields.
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Defines the default primary key field type to be used for models when no explicit primary key is set.
# The 'BigAutoField' allows for larger integers (up to 9223372036854775807) as primary keys, which is useful for applications with a large number of records.
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Static, media, and locale settings.
#########################################################################################################
# Static files settings define how static assets like CSS, JavaScript, and images are served.
STATIC_URL = '/static/'

# The root directory where static files will be collected for deployment.
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Additional directories where static files are stored.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "core/static"),
]

# MEDIA_URL is the URL where files will be accessed from the browser
MEDIA_URL = '/media/'

# MEDIA_ROOT is the actual filesystem path where the files are stored
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Language and timezone settings.
# Defines the language code for the application and the timezone used for date and time.
LANGUAGE_CODE = 'ar'
TIME_ZONE = 'Etc/GMT-2'
USE_I18N = True
USE_TZ = True

# Default charset for the application. It's set to UTF-8 for international character support.
DEFAULT_CHARSET = 'utf-8'

# Specifies the paths for translation files. 
# This is where the application will look for language files.
# LOCALE_PATHS = [BASE_DIR / 'locale']


# CSP Configuration (for HTML responses)
#########################################################################################################
# CSP Configuration (for HTML responses)
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = (
#     "'self'",
#     "https://cdn.plot.ly",
#     "https://code.jquery.com",  # Allow jQuery and jQuery UI JS
# )
# CSP_STYLE_SRC = (
#     "'self'",
#     "'unsafe-inline'",  # Still needed for Django admin
#     "https://code.jquery.com",  # Allow jQuery UI CSS
# )
# CSP_IMG_SRC = ("'self'", "data:")
# CSP_FONT_SRC = ("'self'",)
# CSP_CONNECT_SRC = ("'self'",)
# CSP_INCLUDE_NONCE_IN = ("script-src",)  # For inline scripts
# CSP_FRAME_SRC = ("'self'",)
# # Critical for hybrid setup:
# CSP_EXCLUDE_URL_PREFIXES = ('/static/',)  # Prevent Django from adding CSP to static files


# Logging settings
#########################################################################################################
# low-level logging settings for the entire Django project.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

VERSION = get_last_version_from_readme()