#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
# encoding=utf-8
import os

PROJECT_PATH = os.path.abspath('%s' % os.path.dirname(__file__))

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #

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

    "pagination",
    "django_sorting",
    "south",
    "django_nose",
    "rosetta",
    "selectable",
    # "gunicorn",
    "aremind.apps.smstouchforms",
    "aremind.apps.groups",
    "aremind.apps.broadcast",
    "aremind.apps.reminders",
    "aremind.apps.patients",
    "aremind.apps.adherence",
    "aremind.apps.test_messager",
    "aremind.apps.default_connection",


    # the rapidsms contrib apps.
    # "rapidsms.contrib.export",
    "threadless_router.backends.httptester",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    # "rapidsms.contrib.registration",
    #"rapidsms.contrib.scheduler",
    "rapidsms.contrib.echo",
    "touchforms.formplayer",
#    "smsforms",

#    "timezones",

    "couchlog",
    # this app should be last, as it will always reply with a help message
    "aremind.apps.catch_all",
]


# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("aremind.apps.broadcast.views.dashboard", "Dashboard"),    
    ("aremind.apps.broadcast.views.send_message", "Send a Message"),
    ("aremind.apps.adherence.views.dashboard", "Adherence"),
    ("aremind.apps.reminders.views.dashboard", "Appointments"),
    ("aremind.apps.patients.views.list_patients", "Patients"),
    ("broadcast-forwarding", "Forwarding"),
    ("aremind.apps.groups.views.list_groups", "Groups"),
    ("aremind.apps.groups.views.list_contacts","People"),
#    ("settings", "Settings"),
#    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log"),

#    ("rapidsms.contrib.messaging.views.messaging",          "Messaging"),
#    ("rapidsms.contrib.locations.views.locations",          "Map"),
#    ("rapidsms.contrib.scheduler.views.index",              "Event Scheduler"),
 #   ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),

#    ("aremind.apps.reminder.views.dashboard", "Reminder"),
]



# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
DEBUG = TEMPLATE_DEBUG = True


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
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(PROJECT_PATH, '..', 'static_files')


# Specify a logo URL for the dashboard layout.html. This logo will show up
# at top left for every tab
LOGO_LEFT_URL = '%simages/blank.png' % STATIC_URL
LOGO_RIGHT_URL = '%simages/blank.png' % STATIC_URL
SITE_TITLE = "ARemind"
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
#    'aremind.login_required_everything.RequireLoginMiddleware',
#    'auditcare.middleware.AuditMiddleware',
]
    
# -------------------------------------------------------------------- #
#                           HERE BE DRAGONS!                           #
#        these settings are pure hackery, and will go away soon        #
# -------------------------------------------------------------------- #

AJAX_PROXY_HOST = '127.0.0.1'
AJAX_PROXY_PORT = 9988

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')

TEMPLATE_DIRS = [
    os.path.join(PROJECT_PATH, 'templates'),
]

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

#RAPIDSMS_HANDLERS_EXCLUDE_APPS = ["couchlog","djcelery"]

STATICFILES_FINDERS =(
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

PYTHON_ENV_PATH = os.path.join(PROJECT_PATH,'..','..','python_env')
DJ_SELECTABLE_STATIC_PATH = os.path.join(PYTHON_ENV_PATH,'src','django-selectable','selectable','static')

STATICFILES_DIRS = (os.path.join(PROJECT_PATH, 'static'),
                    os.path.join(PROJECT_PATH, 'templates'),
                    os.path.join(DJ_SELECTABLE_STATIC_PATH))




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

import djcelery
djcelery.setup_loader()

from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    "adherence-reminder-scheduler": {
        "task": "aremind.apps.adherence.tasks.ReminderSchedulerTask",
        "schedule": crontab(),
    },
    "adherence-update-feeds": {
        "task": "aremind.apps.adherence.tasks.FeedUpdatesTask",
        "schedule": crontab(minute=15), # Quarter after every hour
    },
    "broadcast-task": {
        "task": "aremind.apps.broadcast.tasks.BroadcastCronTask",
        "schedule": crontab(), # every minute
    },
    "reminders-scheduler-task": {
        "task": "aremind.apps.reminders.tasks.ReminderSchedulerTask",
        "schedule": crontab(), # every minute
    },
#    "reminders-email-task": {
#        "task": "aremind.apps.reminders.tasks.ReminderEmailTask",
#        "schedule": crontab(hour=12, minute=0),
#    },
    "decisiontree-tick": {
        "task": "decisiontree.tasks.PeriodicTask",
        "schedule": crontab(),  # every minute
    },
}

# Store the schedule in the Django database
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

CELERYD_MAX_TASKS_PER_CHILD = 2

INSTALLED_BACKENDS = {}

#STATICFILES_EXCLUDED_APPS = (
#    'django.contrib.admin',
#)

DEFAULT_MESSAGE = "Unfortunately, we did not understand your message. Please call Elizabeth at 617 414 7022 if you need help."

AUDIT_DJANGO_USER = True
AUDIT_MODEL_SAVE = []

NO_LOGIN_REQUIRED_FOR = ["/tropo",
                         "/tropo/",
                         "/ajax/",
                         "/ajax",]


XFORMS_PLAYER_URL = "http://127.0.0.1:4444"