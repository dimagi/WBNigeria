
#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import os

PROJECT_PATH = os.path.abspath('%s' % os.path.dirname(__file__))
FORMDESIGNER_ROOT = os.path.join(PROJECT_PATH, '..', 'submodules', 'formdesigner')

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "wbnigeria",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": ""
    }
}

VERSION = '0.2.1' #This doesn't do anything yet, but what the hey.

BROADCAST_SENDER_BACKEND='message_tester'

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [
    "aremind.apps.wisepill",

    # the essentials.
    "djtables",
    "rapidsms",

    "djcelery",
    "threadless_router.celery",
    "decisiontree",

    #audit utils
#    "auditcare",

    # common dependencies (which don't clutter up the ui).
    "rapidsms.contrib.handlers",
    # "rapidsms.contrib.ajax",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",

    "django.contrib.humanize",
    "django.contrib.flatpages",

    "pagination",
    "django_sorting",
    "south",
    "django_nose",
    "rosetta",
    "selectable",
    "gunicorn",
    "tastypie",

    "rapidsms_xforms",
    "smsforms",

    "alerts",
    "aremind.apps.wbn_registration",
    "aremind.apps.groups",
    "aremind.apps.broadcast",
    "aremind.apps.reminders",
    "aremind.apps.patients",
    "aremind.apps.adherence",
    "aremind.apps.test_messager",
    "aremind.apps.default_connection",
    "aremind.apps.web_users",
    "aremind.apps.reimbursement",

    "eav",
    "uni_form",
    "django_digest",


    # the rapidsms contrib apps.
    # "rapidsms.contrib.export",
    "threadless_router.backends.httptester",
    "threadless_router.backends.kannel",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    # "rapidsms.contrib.registration",
    #"rapidsms.contrib.scheduler",
    "rapidsms.contrib.echo",
    "touchforms.formplayer",
    "smscouchforms",
    "couchforms",
    "couchexport",
#    "smsforms",

#    "timezones",

    "couchlog",
    "aremind.apps.dashboard",
    # this app should be last, as it will always reply with a help message
    "aremind.apps.catch_all",
]


# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    #("aremind.apps.broadcast.views.dashboard", "Dashboard"), # Old dashboard
    ("smscouchforms.views.download",       "View Data", "is_superuser"),
    ("threadless_router.backends.httptester.views.generate_identity", "Message Tester", "is_superuser"),
    ('xforms', 'Reporter Scenario', "is_superuser"),
    ('smsforms.views.list_forms', 'Decision Tree XForms', "is_superuser"),
    ('smsforms.views.view_triggers', 'Decision Tree Triggers', "is_superuser"),
    ('pbf_dashboard', 'PBF Dashboard', 'dashboard.pbf_view'),
    ('fadama_dashboard', 'Fadama Dashboard', 'dashboard.fadama_view'),
]

XFORMS_HOST = 'www.rapidsms-server.com'

# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = True

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)


# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"


# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
TEST_RUNNER = "django_nose.NoseTestSuiteRunner"


# for some reason this setting is blank in django's global_settings.py,
# but it is needed for static assets to be linkable.
MEDIA_URL = "/media/"
ADMIN_MEDIA_PREFIX = "/static/admin/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, '..', 'media')

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, '..', 'static_files')

STATICFILES_FINDERS =(
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_DIRS = (
    os.path.join(PROJECT_PATH, 'static'),
    ('formdesigner', FORMDESIGNER_ROOT),
    ('formdesigner', os.path.join(FORMDESIGNER_ROOT, 'lib', 'xpath')),
)

# Specify a logo URL for the dashboard layout.html. This logo will show up
# at top left for every tab
LOGO_LEFT_URL = '%simages/blank.png' % STATIC_URL
LOGO_RIGHT_URL = '%simages/blank.png' % STATIC_URL
SITE_TITLE = "MyVoice Nigeria"
BASE_TEMPLATE = "layout.html"

# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1


# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",

    #this is for a custom logo on the dashboard (see LOGO_*_URL in settings, above)
    "rapidsms.context_processors.logo",
    "aremind.apps.reminders.context_processors.messages",
#    "couchlog.context_processors.static_workaround"
]


MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django_sorting.middleware.SortingMiddleware',
    'aremind.middleware.AccessControlMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
#    'aremind.login_required_everything.RequireLoginMiddleware',
#    'auditcare.middleware.AuditMiddleware',
]

# -------------------------------------------------------------------- #
#                           HERE BE DRAGONS!                           #
#        these settings are pure hackery, and will go away soon        #
# -------------------------------------------------------------------- #

AJAX_PROXY_HOST = '127.0.0.1'
AJAX_PROXY_PORT = 9988

TEMPLATE_DIRS = (
    os.path.join(PROJECT_PATH, 'templates'),
)

# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    "rapidsms.contrib.ajax",
    "rapidsms.contrib.httptester",
]

# the project-level url patterns

LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', 'English'),
    ('th', 'Thai'),
    ('tl', 'Filipino'),
)

TIME_INPUT_FORMATS = ['%H:%M', '%H:%M:%S']

ROOT_URLCONF = "aremind.urls"

TIME_ZONE = 'America/New_York'

LOGIN_URL = '/account/login/'
REQUIRE_LOGIN_PATH = LOGIN_URL

SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'aremind.migrations.rapidsms',
    'locations': 'aremind.migrations.locations',
    'alerts': 'aremind.migrations.alerts',
}


#The default group subjects are added to when their information
#is POSTed to us
DEFAULT_SUBJECT_GROUP_NAME = 'Patients'
DEFAULT_DAILY_REPORT_GROUP_NAME = 'Daily Report Recipients'
DEFAULT_MONTHLY_REPORT_GROUP_NAME = 'Monthly Report Recipients'
DEFAULT_CONFIRMATIONS_GROUP_NAME = 'Confirmation Recipients'

#The default backend to be used when creating new patient contacts
#on POST submission of patient data from their server
DEFAULT_BACKEND_NAME = "tropo"
# unless overridden, all outgoing messages will be sent using this backend
PRIMARY_BACKEND = 'tropo'
# if set, the message tester app will always use this backend
TEST_MESSAGER_BACKEND = 'tropo'

SMSTOOLS_URL = "http://127.0.0.1:8888/"
INSTALLED_BACKENDS = {
    "httptester": {
        "ENGINE": "threadless_router.backends.httptester.backend",
    },
    "smstools-airtel": {
        "ENGINE": "threadless_router.backends.kannel.outgoing",
        "sendsms_url": SMSTOOLS_URL,
        "sendsms_params": {"modem": "airtel"},
    },
    "smstools-mtn": {
        "ENGINE": "threadless_router.backends.kannel.outgoing",
        "sendsms_url": SMSTOOLS_URL,
        "sendsms_params": {"modem": "mtn"},
    },
    "smstools-etisalat": {
        "ENGINE": "threadless_router.backends.kannel.outgoing",
        "sendsms_url": SMSTOOLS_URL,
        "sendsms_params": {"modem": "etisalat"},
    },
}

DEFAULT_MESSAGE = "Please enter your location code so MyVoice can help you."

#RAPIDSMS_HANDLERS_EXCLUDE_APPS = ["couchlog","djcelery"]

AUDIT_VIEWS = [
    'aremind.apps.adherence.views.create_edit_schedule',
    'aremind.apps.adherence.views.delete_schedule',
    'aremind.apps.adherence.views.create_edit_feed',
    'aremind.apps.adherence.views.delete_feed',
    'aremind.apps.adherence.views.create_edit_entry',
    'aremind.apps.adherence.views.delete_entry',
    'aremind.apps.adherence.views.ivr_callback',
    'aremind.apps.adherence.views.query_results',
    'aremind.apps.adherence.views.create_edit_query_schedule',
    'aremind.apps.adherence.views.delete_query_schedule',
    'aremind.apps.adherence.views.force_query_schedule',
    'aremind.apps.adherence.views.pills_missed_report',
    'aremind.apps.adherence.views.wisepill_by_last_report',
    'aremind.apps.adherence.views.dashboard',
    'aremind.apps.broadcast.views.send_message',
    'aremind.apps.broadcast.views.schedule',
    'aremind.apps.broadcast.views.delete_broadcast',
    'aremind.apps.broadcast.views.create_edit_rule',
    'aremind.apps.broadcast.views.delete_rule',
    'aremind.apps.broadcast.views.report_graph_data',
    'aremind.apps.broadcast.views.last_messages',
    'aremind.apps.groups.create_edit_group',
    'aremind.apps.groups.views.delete_group',
    'aremind.apps.groups.views.create_edit_contact',
    'aremind.apps.groups.views.delete_contact'
    'aremind.apps.patients.views.create_edit_patient',
    'aremind.apps.patients.views.create_edit_pill_history',
    'aremind.apps.patients.views.patient_onetime_message',
    'aremind.apps.patients.views.patient_start_adherence_tree',
    'aremind.apps.patients.views.messages_to_patient',
    'aremind.apps.reminders.views.create_edit_notification',
    'aremind.apps.reminders.views.delete_notification',
    'aremind.apps.reminders.views.manually_confirm',
    'aremind.apps.reminders.views.dashboard',
    'aremind.apps.wisepill.views.list_messages_for_patient',
    'aremind.apps.test_messager.views.message_form'
]


# Store the schedule in the Django database
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERYD_MAX_TASKS_PER_CHILD = 2

DECISION_TREE_TRIGGER_KEYWORDS = {
    'fadama': '4',
    'health': '3',
}

AUDIT_DJANGO_USER = True
AUDIT_MODEL_SAVE = []

NO_LOGIN_REQUIRED_FOR = (
    "/tropo",
    "/tropo/",
    "/ajax/",
    "/ajax",
)


XFORMS_PLAYER_URL = "http://127.0.0.1:4444"
BROKER_URL = "amqp://guest:guest@localhost:5672//"

GMAPS_API_KEY = ''

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {

#        %(name)s            Name of the logger (logging channel)
#        %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
#                            WARNING, ERROR, CRITICAL)
#        %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
#                            "WARNING", "ERROR", "CRITICAL")
#        %(pathname)s        Full pathname of the source file where the logging
#                            call was issued (if available)
#        %(filename)s        Filename portion of pathname
#        %(module)s          Module (name portion of filename)
#        %(lineno)d          Source line number where the logging call was issued
#                            (if available)
#        %(funcName)s        Function name
#        %(created)f         Time when the LogRecord was created (time.time()
#                            return value)
#        %(asctime)s         Textual time when the LogRecord was created
#        %(msecs)d           Millisecond portion of the creation time
#        %(relativeCreated)d Time in milliseconds when the LogRecord was created,
#                            relative to the time the logging module was loaded
#                            (typically at application startup time)
#        %(thread)d          Thread ID (if available)
#        %(threadName)s      Thread name (if available)
#        %(process)d         Process ID (if available)
#        %(message)s         The result of record.getMessage(), computed just as
#                            the record is emitted
        'verbose': {
            # %(process)d %(thread)d
            'format': '%(levelname)s %(asctime)s - [%(module)s] - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - [%(module)s] - %(message)s'
        },
    },
    'filters': {
#        'special': {
#            '()': 'project.logging.SpecialFilter',
#            'foo': 'bar',
#        }
    },
    'handlers': {
#        'null': {
#            'level':'DEBUG',
#            'class':'django.utils.log.NullHandler',
#        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
#            'filters': ['special']
        }
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
#        'aremind': {
#            'handlers': ['console', 'mail_admins'],
#            'level': 'DEBUG',
#            'formatter': 'verbose'
##            'filters': ['special']
#        },
        'backend/httptester': {
                    'handlers': ['console'],
                    'level': 'INFO',
                    'formatter': 'verbose'
        #            'filters': ['special']
        },
        'backend/smstools': {
                    'handlers': ['console'],
                    'level': 'DEBUG',
                    'formatter': 'verbose'
        #            'filters': ['special']
        },
        'app.wbn_registration' : {
            'handlers': ['console'],
            'level': 'DEBUG',
            'formatter': 'verbose'
                #            'filters': ['special']
        },
        'router' : {
            'handlers': ['console'],
            'level': 'DEBUG',
            'formatter': 'verbose'
        },
        'xformsresponse': {
                    'handlers': ['console'],
                    'level': 'DEBUG',
                    'formatter': 'verbose'
                },
    }
}

COUCHDB_APPS = ['auditcare', 'couchlog', 'formplayer', 'couchforms', 'couchexport']


from datetime import timedelta

# search for other reports from same phone number within this time window for 'there are N other recent reports...' warning
RECENT_REPORTS_FROM_SAME_PHONE_WINDOW = timedelta(weeks=6)

# time window after officer sends inquiry to beneficiary via sms to consider the thread 'open'. beneficiary responses received
# outside of this window will be thrown out
COMMUNICATOR_RESPONSE_WINDOW = timedelta(weeks=3)

# show warning if officer tries to use communicator on a report that has not seen any activity (initial submit or beneficiary response)
# beyond this time window
COMMUNICATOR_TOO_OLD_WINDOW = timedelta(weeks=6)

# rapidsms-alerts app.
LOGISTICS_NOTIF_GENERATORS = (
    'aremind.notifications.idle_facilities.fadama_idle_facilities',
    'aremind.notifications.idle_facilities.pbf_idle_facilities',
    'aremind.notifications.digests.fadama_digest_notifications',
    'aremind.notifications.digests.pbf_digest_notifications',
)
LOGISTICS_ALERT_GENERATORS = (
    'aremind.notifications.recent.recent_fadama_activity',
    'aremind.notifications.recent.recent_pbf_activity',
)
SYSTEM_USERNAME = "the_man"

DECISION_TREE_FORMS = {
    'fadama': 'http://openrosa.org/formdesigner/Fadama',
    'pbf': 'http://openrosa.org/formdesigner/PBF',
}

from datetime import timedelta
SMSFORMS_POSTSESSION_LOCKOUT = timedelta(hours=24)

NETWORK_PREFIXES = {
    '234701': 'airtel',
    '234703': 'mtn',
    '234706': 'mtn',
    '234708': 'airtel',
    '234802': 'airtel',
    '234803': 'mtn',
    '234806': 'mtn',
    '234808': 'airtel',
    '234809': 'etisalat',
    '234810': 'mtn',
    '234812': 'airtel',
    '234813': 'mtn',
    '234814': 'mtn',
    '234816': 'mtn',
    '234817': 'etisalat',
    '234818': 'etisalat',
}

REIMBURSED_BACKENDS = ['smstools-mtn', 'smstools-airtel', 'smstools-etisalat']
NETWORK_PINS = {
    'mtn': '0205',
    'airtel': '3217',
    'etisalat': ''
    }
MINIMUM_TRANSFERS = {
    'mtn': 50,
    'airtel': 50,
    'etisalat': 50
    }
REIMBURSEMENT_RATES = {
    'mtn': 4,
    'airtel': 4,
    'etisalat': 4,
}
