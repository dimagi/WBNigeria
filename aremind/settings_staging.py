from aremind.settings import *

ADMINS = (
    ('Development Team', 'aremind-dev@dimagi.com'),
)
MANAGERS = ADMINS

INSTALLED_BACKENDS = {
    "twilio": {
        "ENGINE": "rtwilio.backend",
        'host': 'localhost', 'port': '8081', # used for spawned backend WSGI server
        'config': {
            'encoding' : 'UTF-8'
        }
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "aremind_staging",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}

#The default backend to be used when creating new patient contacts
#on POST submission of patient data from their server
DEFAULT_BACKEND_NAME = "twilio"
# unless overridden, all outgoing messages will be sent using this backend
PRIMARY_BACKEND = "twilio"

DEBUG = True

LOG_LEVEL = "DEBUG"
LOG_FILE = '/home/aremind/www/staging/log/router.log'
LOG_FORMAT = "%(asctime)s %(levelname)-8s - %(name)-26s %(message)s"
LOG_SIZE = 33554432 # 2^25
LOG_BACKUPS = 10 # number of logs to keep

COUNTRY_CODE = '1'
