import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    #('Your Name', 'your_email@example.com'),
)

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dev.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

TIME_ZONE = 'America/New_York'

MEDIA_ROOT = ''
MEDIA_URL = ''
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
STATIC_URL = '/static/'

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

API_MASTER_KEY = ''

GA_CONFIG = os.path.join(PROJECT_ROOT, '')
GA_EMAIL = ''
GA_PASSWORD = ''

RATIOS_CONFIG = os.path.join(PROJECT_ROOT, '')