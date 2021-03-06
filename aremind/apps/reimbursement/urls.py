from django.conf.urls.defaults import *
from aremind.apps.reimbursement import views


urlpatterns = patterns('',
    url(r'^getbatch/$', views.get_next_batch, name='reimbursement-batch'),
    url(r'^start/$', views.start_reimbursement, name='reimbursement-start'),
    #url(r'^schedule/(?P<broadcast_id>\d+)/edit/$', views.send_message,
    #    name='edit-broadcast'),
    #url(r'^schedule/(?P<broadcast_id>\d+)/delete/$', views.delete_broadcast,
    #    name='delete-broadcast'),
    #url(r'^messages/$', views.list_messages, name='broadcast-messages'),
    #url(r'^forwarding/$', views.forwarding,
    #    name='broadcast-forwarding'),
    #url(r'^forwarding/create/$', views.create_edit_rule,
    #    name='broadcast-forwarding-create'),
    #url(r'^forwarding/(?P<rule_id>\d+)/edit/$', views.create_edit_rule,
    #    name='broadcast-forwarding-edit'),
    #url(r'^forwarding/(?P<rule_id>\d+)/delete/$', views.delete_rule,
    #    name='broadcast-forwarding-delete'),
    #url('^usage-data/$', views.report_graph_data,
    #    name='broadcast-usage-graph-data'),
    #url('^message-data/$', views.last_messages,
    #    name='broadcast-usage-recent-messages'),
)
