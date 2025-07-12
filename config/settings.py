# config/settings.py - Professional Django Configuration with Fixed Media Serving
"""
Django settings for Connectify social media platform.

This configuration supports:
- JWT Authentication with React frontend
- Real-time messaging via Django Channels
- Media file uploads (avatars, posts)
- AWS SES email integration
- PostgreSQL database
- CORS enabled for React development
- Razorpay payment integration

For production deployment, ensure to:
- Set DEBUG = False
- Configure proper ALLOWED_HOSTS
- Use environment-specific database settings
- Set up proper static/media serving (nginx/apache)
"""

import os
from pathlib import Path
from decouple import config
from datetime import timedelta

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-f_r=5^5qg2m#(14-a-c(ay!rs2z(v_xwro2r&5n-5e2pqep5q8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Hosts allowed to access this Django application
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    # Add your production domain here when deploying
]

# Custom User Model - Tell Django to use our custom User model
AUTH_USER_MODEL = 'authentication.User'

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    # Django Channels must be first for ASGI support
    'daphne',
    
    # Django built-in applications
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party applications
    'rest_framework',              # Django REST Framework for API
    'rest_framework_simplejwt',    # JWT authentication
    'corsheaders',                 # CORS headers for React frontend
    'channels',                    # WebSocket support for real-time features
    
    # Custom applications
    'core',                        # Core app (posts, likes, comments)
    'authentication',              # User authentication and profiles
    'messaging',                   # Real-time messaging system
    'notifications',               # Push notifications system
    'payments.apps.PaymentsConfig'                 # Razorpay payment integration
]

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    # CORS middleware must be first to handle preflight requests
    'corsheaders.middleware.CorsMiddleware',
    
    # Django built-in middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

# =============================================================================
# TEMPLATE CONFIGURATION
# =============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Add custom templates directory
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

# =============================================================================
# WSGI/ASGI CONFIGURATION
# =============================================================================

# Traditional WSGI application (for standard HTTP requests)
WSGI_APPLICATION = 'config.wsgi.application'

# ASGI application (for WebSockets and real-time features)
ASGI_APPLICATION = 'config.asgi.application'

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='connectify_aws'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='N4qhtnqd123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 60,                 # Connection timeout (seconds)
            'application_name': 'connectify',      # Application identifier
            'sslmode': 'prefer',                   # SSL preference for security
        },
        'CONN_MAX_AGE': 600,                      # Keep connections alive (seconds)
    }
}

# =============================================================================
# DJANGO CHANNELS CONFIGURATION (Real-time Features)
# =============================================================================

# Channel layers for WebSocket support
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            "capacity": 1500,           # Max messages per channel
            "expiry": 60,               # Message expiry in seconds
            "group_expiry": 86400,      # Group expiry (24 hours)
            "symmetric_encryption_keys": [SECRET_KEY],  # Optional encryption
        },
    }
}
# =============================================================================
# REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    # Authentication classes (in order of preference)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API
    ],
    
    # Default permissions (require authentication)
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    
    # Response rendering
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # For development
    ],
    
    # Request parsing (handles file uploads)
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',        # For file uploads
        'rest_framework.parsers.FormParser',
    ],
    
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    
    # Filtering and ordering
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
}

# =============================================================================
# JWT AUTHENTICATION CONFIGURATION
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),        # Access token validity
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),         # Refresh token validity
    'ROTATE_REFRESH_TOKENS': True,                       # Generate new refresh token on use
    'BLACKLIST_AFTER_ROTATION': True,                    # Blacklist old refresh tokens
    'UPDATE_LAST_LOGIN': True,                           # Update user's last_login field
    
    # Token configuration
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    # Header configuration
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # User identification
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
}

# =============================================================================
# RAZORPAY CONFIGURATION
# =============================================================================

RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='rzp_test_kgUSjYv0BpQTJA')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='x2ga0ePmzBaTDzOa8ifPKtyb')

RAZORPAY_SETTINGS = {
    'CURRENCY': 'INR',
    'PAYMENT_TIMEOUT': 300,  # 5 minutes
    'SUBSCRIPTION_AMOUNT': 1000,  # ₹10 in paise
    'RECEIPT_PREFIX': 'connectify_',
}

# =============================================================================
# CORS CONFIGURATION (React Frontend Communication)
# =============================================================================

# Allow React development server to make requests
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React development server
    "http://127.0.0.1:3000",     # Alternative localhost format
    # Add your production frontend domain here
]

# CORS settings for development
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins in development
    
CORS_ALLOW_CREDENTIALS = True      # Allow cookies and auth headers
CORS_ALLOW_ALL_HEADERS = True      # Allow all request headers

# =============================================================================
# STATIC AND MEDIA FILES CONFIGURATION
# =============================================================================

# FIXED: Use relative URLs for proper Django routing
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# File system paths
STATIC_ROOT = BASE_DIR / 'staticfiles'           # Collected static files (production)
MEDIA_ROOT = BASE_DIR / 'media'                  # User uploaded files

# Additional static files directories (development)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB max file size in memory
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10MB max request size
FILE_UPLOAD_PERMISSIONS = 0o644                   # File permissions for uploads

# =============================================================================
# EMAIL CONFIGURATION (AWS SES)
# =============================================================================

# SMTP backend for AWS SES
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.eu-north-1.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('AWS_ACCESS_KEY_ID', default='')
EMAIL_HOST_PASSWORD = config('AWS_SECRET_ACCESS_KEY', default='')

# Email addresses
DEFAULT_FROM_EMAIL = 'rob063838@gmail.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

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

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

if DEBUG:
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
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': BASE_DIR / 'logs' / 'django.log',
                'formatter': 'verbose',
            } if (BASE_DIR / 'logs').exists() else {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG' if DEBUG else 'INFO',
                'propagate': False,
            },
            # Custom app loggers
            'core': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'authentication': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'messaging': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
            'payments': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
    }

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

if not DEBUG:
    # Production security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# DEVELOPMENT-SPECIFIC SETTINGS
# =============================================================================

if DEBUG:
    # Allow all hosts in development
    ALLOWED_HOSTS = ['*']
    
    # Additional development apps
    try:
        import debug_toolbar
        INSTALLED_APPS.append('debug_toolbar')
        MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass

# =============================================================================
# DEFAULT FIELD TYPES
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# CUSTOM APPLICATION SETTINGS
# =============================================================================

# File upload constraints
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_TYPES = ['JPEG', 'JPG', 'PNG', 'GIF', 'WEBP']
ALLOWED_VIDEO_TYPES = ['MP4', 'WEBM', 'OGV']

# Post content limits
MAX_POST_LENGTH = 2200
MAX_COMMENT_LENGTH = 500
MAX_BIO_LENGTH = 150

# Pagination settings
POSTS_PER_PAGE = 20
COMMENTS_PER_PAGE = 10
FOLLOWERS_PER_PAGE = 20

# Cache settings (for production)
if not DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'KEY_PREFIX': 'connectify',
            'TIMEOUT': 300,  # 5 minutes default timeout
        }
    }

# =============================================================================
# ENVIRONMENT-SPECIFIC CONFIGURATIONS
# =============================================================================

# Load environment-specific settings if they exist
try:
    if DEBUG:
        from .local_settings import *
    else:
        from .production_settings import *
except ImportError:
    pass

# =============================================================================
# FINAL VALIDATION
# =============================================================================

# Ensure media directory exists
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
(MEDIA_ROOT / 'avatars').mkdir(exist_ok=True)
(MEDIA_ROOT / 'posts' / 'images').mkdir(parents=True, exist_ok=True)

# Create logs directory if logging to file
if DEBUG and 'file' in [h.get('class', '') for h in LOGGING.get('handlers', {}).values()]:
    (BASE_DIR / 'logs').mkdir(exist_ok=True)