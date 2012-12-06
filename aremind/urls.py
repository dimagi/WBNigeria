from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template

from aremind.apps.dashboard.views import pbf
from aremind.apps.dashboard.views import fadama

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^my-project/', include('my_project.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),
#    (r'^', include('decisiontree.urls')),

    # RapidSMS core URLs
    url(r'^account/login/', 'rapidsms.views.login', name='rapidsms_login'),
    url(r'^account/logout/', 'rapidsms.views.logout', name='rapidsms_logout'),
    (r'^account/', include('rapidsms.urls.login_logout')),
    url(r'old/$', 'aremind.apps.broadcast.views.dashboard', name='broadcast-dashboard'),
    url(r'^welcome/$', 'aremind.apps.web_users.views.welcome'),
    url(r'^$', 'smscouchforms.views.download', name='rapidsms-dashboard'),

    url(r'^settings/$', direct_to_template,
        {'template': 'aremind/not_implemented.html'}, name='settings'),

    # RapidSMS contrib app URLs
    (r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    url(r'^httptester/$',
        'threadless_router.backends.httptester.views.generate_identity',
        {'backend_name': 'httptester'}, name='httptester-index'),
    (r'^httptester/', include('threadless_router.backends.httptester.urls')),
    (r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),
    (r'^registration/', include('rapidsms.contrib.registration.urls')),
#    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^broadcast/', include('aremind.apps.broadcast.urls')),
#    (r'^adherence/', include('aremind.apps.adherence.urls')),
    (r'^appointments/', include('aremind.apps.reminders.urls')),
    (r'^patients/', include('aremind.apps.patients.urls')),
    (r'^wisepill/', include('aremind.apps.wisepill.urls')),
    (r'^test-messager/', include('aremind.apps.test_messager.urls')),
    (r'^crm/', include('aremind.apps.groups.urls')),
    (r'^rosetta/', include('rosetta.urls')),
    (r'^selectable/', include('selectable.urls')),
    (r'^webforms/', include('touchforms.formplayer.urls')),
    (r'^smsforms/', include('smsforms.urls')),
    (r'^alerts/', include('alerts.urls')),
    ('', include('rapidsms_xforms.urls')),
    (r'^smscouchforms/', include('smscouchforms.urls')),
    (r'^couchexport/', include("couchexport.urls")),
    url(r'^tropo/$', 'rtropo.views.message_received', kwargs={'backend_name': 'tropo'}, name='tropo'),

    url(r'dashboard/pbf/$', pbf.DashboardView.as_view(), name='pbf_dashboard'),
    url(r'dashboard/fadama/$', fadama.DashboardView.as_view(), name='fadama_dashboard'),
    (r'^dashboard/', include('aremind.apps.dashboard.urls')),
)


if 'couchlog' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^couchlog/', include('couchlog.urls')),
    )


if 'auditcare' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^', include('auditcare.urls')),
    )


 # Contrib Auth Password Management
urlpatterns += patterns('django.contrib.auth.views',
    url(r'^account/password/change/$', 'password_change', name='auth_password_change'),
    url(r'^account/password/change/done/$', 'password_change_done', name='auth_password_change_done'),
    url(r'^account/password/reset/$', 'password_reset', name='auth_password_reset'),
    url(r'^account/password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm',
        name='auth_password_reset_confirm'),
    url(r'^account/password/reset/complete/$', 'password_reset_complete', name='auth_password_reset_complete'),
    url(r'^account/password/reset/done/$', 'password_reset_done', name='auth_password_reset_done'),
)

FORMDESIGNER_PATH = getattr(settings, 'FORMDESIGNER_ROOT', 'C:\\Users\\adewinter\\workspace-dimagi\\wbnigeria\\submodules\\formdesigner')
if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
        (r'^formdesigner/(?P<path>.*)',
         'django.views.static.serve',
         {'document_root': FORMDESIGNER_PATH, 'show_indexes': True}
        ),
        (r'^%s(?P<path>.*)' % settings.MEDIA_URL.lstrip('/'),
         'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}
        ),
    )

    # For testing
    urlpatterns += patterns('',
        # ...
        url(r'^httptester/$',
            'threadless_router.backends.httptester.views.generate_identity',
            {'backend_name': 'httptester'}, name='httptester-index'),
        (r'^httptester/', include('threadless_router.backends.httptester.urls')),
        # ...
    )
