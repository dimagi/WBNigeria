from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.adherence.views',
    url(r'^create/$', 'create_edit_schedule', name='adherence-create-reminder'),
    url(r'^edit/(?P<reminder_id>\d+)/$', 'create_edit_schedule', name='adherence-edit-reminder'),
    url(r'^delete/(?P<reminder_id>\d+)/$', 'delete_schedule', name='adherence-delete-reminder'),
    url(r'^$', 'dashboard', name='adherence-dashboard'),
)
