from aremind.settings import *

ADMINS = (
    ('Development Team', 'aremind-dev@dimagi.com'),
)
MANAGERS = ADMINS

INSTALLED_BACKENDS = {
    "tropo": {
        "ENGINE": "rtropo.outgoing",
        'config': {
            'encoding' : 'UTF-8',
            'number': '+1-919-500-7767',
            'messaging_token': 'xxxx',
        }
    },
}

RAPIDSMS_HANDLERS_EXCLUDE_APPS = []

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "aremind_staging",
        "USER": "aremind",
        "PASSWORD": "", # In local settings
        "HOST": "",
        "PORT": "",
    },
}

#The default backend to be used when creating new patient contacts
#on POST submission of patient data from their server
DEFAULT_BACKEND_NAME = "tropo"
# unless overridden, all outgoing messages will be sent using this backend
PRIMARY_BACKEND = "tropo"

DEBUG = True

LOG_LEVEL = "DEBUG"
LOG_FILE = '/home/aremind/www/staging/log/router.log'
LOG_FORMAT = "%(asctime)s %(levelname)-8s - %(name)-26s %(message)s"
LOG_SIZE = 33554432 # 2^25
LOG_BACKUPS = 10 # number of logs to keep

COUNTRY_CODE = '1'

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_VHOST = "aremind_staging"
BROKER_USER = "aremind"
BROKER_PASSWORD = "" # In local settings
