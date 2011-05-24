from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.adherence.views',
    url(r'^schedules/create/$', 'create_edit_schedule', name='adherence-create-reminder'),
    url(r'^schedules/edit/(?P<reminder_id>\d+)/$', 'create_edit_schedule', name='adherence-edit-reminder'),
    url(r'^schedules/delete/(?P<reminder_id>\d+)/$', 'delete_schedule', name='adherence-delete-reminder'),
    url(r'^feeds/create/$', 'create_edit_feed', name='adherence-create-feed'),
    url(r'^feeds/edit/(?P<feed_id>\d+)/$', 'create_edit_feed', name='adherence-edit-feed'),
    url(r'^feeds/delete/(?P<feed_id>\d+)/$', 'delete_feed', name='adherence-delete-feed'),
    url(r'^feeds/(?P<feed_id>\d+)/$', 'view_feed', name='adherence-view-feed'),
    url(r'^entries/create/(?P<feed_id>\d+)/$', 'create_edit_entry', name='adherence-create-entry'),
    url(r'^entries/edit/(?P<entry_id>\d+)/$', 'create_edit_entry', name='adherence-edit-entry'),
    url(r'^entries/delete/(?P<entry_id>\d+)/$', 'delete_entry', name='adherence-delete-entry'),
    url(r'^ivr/callback/$', 'ivr_callback', name='adherence-ivr-callback'),
    url(r'^query_results/$', 'query_results', name='adherence-query-results'),
    url(r'^query_schedule_create/$', 'create_edit_query_schedule', name='adherence-create-query-schedule'),
    url(r'^query_schedule_edit/(?P<schedule_id>\d+)/$', 'create_edit_query_schedule', name='adherence-edit-query-schedule'),
    url(r'^query_schedule_delete/(?P<schedule_id>\d+)/$', 'delete_query_schedule', name='adherence-delete-query-schedule'),
    url(r'^query_schedule_force/(?P<schedule_id>\d+)/$', 'force_query_schedule', name='adherence-force-query-schedule'),
    url(r'^$', 'dashboard', name='adherence-dashboard'),
)
