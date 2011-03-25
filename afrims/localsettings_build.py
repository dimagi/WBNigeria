from afrims.settings import *

# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

# for sqlite3:
#DATABASES = {
#    "default": {
#        "ENGINE": "django.db.backends.sqlite3",
#        "NAME": "db.sqlite3",
#        "USER": "",
#        "PASSWORD": "",
#        "HOST": "",
# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
#        "TEST_NAME": "test_db.sqlite3",
#    }
#}


# for postgresql:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "trialconnectdb",
        "USER": "hqdbuser",
        "PASSWORD": "buildme",
        "HOST": "localhost",
    }
}

TESTING_DATABASES= {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",#
        "NAME": "afrims.sqlite3",
    }
}

INSTALLED_BACKENDS = {
    #"att": {
    #    "ENGINE": "rapidsms.backends.gsm",
    #    "PORT": "/dev/ttyUSB0"
    #},
    #"verizon": {
    #    "ENGINE": "rapidsms.backends.gsm,
    #    "PORT": "/dev/ttyUSB1"
    #},
	#"droid": {
	#            "ENGINE": "rapidsms.backends.droid",
	#            "AP_PORT": '9999',
	#            "SERVER_PORT": '55625',
	#    }
	
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
    "txtnation" : {"ENGINE":  "rapidsms.backends.http",
                   "host":"0.0.0.0",
            "port": 9088,
            "gateway_url": "http://client.txtnation.com/mbill.php",
            "params_outgoing": "reply=%(reply)s&id=%(id)s&network=%(network)s&number=%(phone_number)s&message=%(message)s&ekey=<SECRET_EKEY>&cc=dimagi&currency=THB&value=0&title=trialcnct",
            "params_incoming": "action=action&id=%(id)s&number=%(phone_number)s&network=%(network)s&message=%(message)s&shortcode=%(sc)s&country=%(country_code)&billing=%(bill_code)s"
    },

}

DJANGO_LOG_FILE = "afrims.django.log"
LOG_SIZE = 1000000
LOG_LEVEL   = "DEBUG"
LOG_FILE    = "afrims.router.log"
LOG_FORMAT  = "%(asctime)s - [%(levelname)s]\t[%(name)s]: %(message)s"
LOG_BACKUPS = 256 # number of logs to keep

# MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
# MIDDLEWARE_CLASSES.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# INTERNAL_IPS = ('127.0.0.1',)
# INSTALLED_APPS = list(INSTALLED_APPS)
# INSTALLED_APPS.append('debug_toolbar')
# DEBUG_TOOLBAR_CONFIG = {'INTERCEPT_REDIRECTS': False}
