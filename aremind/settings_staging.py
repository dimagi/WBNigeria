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
            # Tropo application:
            #   account 'aremind'
            #   app 'aremind_staging'
            'number': '+1-919-500-7767',
            'messaging_token': '01ebb5bed919a94f8edd5978adf3766b78c0e260765778034d83dc087ff2c0ad302ed22a19359e56889a8e6e',
            'voice_token': '01eb83b87acdbd459e55e777bf482ff39b3b7e7ea7b071737131e19669b99e7ea0eefa4ec2443e86ca31f143',
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
