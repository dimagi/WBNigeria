from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.adherence.views',
    url(r'^create/$', 'create_edit_schedule', name='adherence-create-reminder-schedule'),
    url(r'^edit/(?P<reminder_id>\d+)/$', 'create_edit_schedule', name='adherence-edit-reminder-schedule'),
    url(r'^$', 'dashboard', name='adherence-dashboard'),
)
