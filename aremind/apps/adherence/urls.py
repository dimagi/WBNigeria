from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.adherence.views',
    url(r'^schedules/create/$', 'create_edit_schedule', name='adherence-create-reminder'),
    url(r'^schedules/edit/(?P<reminder_id>\d+)/$', 'create_edit_schedule', name='adherence-edit-reminder'),
    url(r'^schedules/delete/(?P<reminder_id>\d+)/$', 'delete_schedule', name='adherence-delete-reminder'),
    url(r'^feeds/create/$', 'create_edit_feed', name='adherence-create-feed'),
    url(r'^feeds/edit/(?P<feed_id>\d+)/$', 'create_edit_feed', name='adherence-edit-feed'),
    url(r'^$', 'dashboard', name='adherence-dashboard'),
)
