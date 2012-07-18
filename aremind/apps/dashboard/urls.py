from django.conf.urls.defaults import *

from aremind.apps.dashboard.views import fadama
from aremind.apps.dashboard.views import pbf

urlpatterns = patterns('',
    url(r'^pbf/$', pbf.DashboardView.as_view(), name='pbf_dashboard'),
    url(r'^pbf/reports/$', pbf.ReportView.as_view(), name='pbf_reports'),

    url(r'^pbf/api/main/$', pbf.api_main),
    url(r'^pbf/api/detail/$', pbf.api_detail),

    url(r'^fadama/$', fadama.DashboardView.as_view(), name='fadama_dashboard'),
    url(r'^fadama/reports/$', fadama.ReportView.as_view(), name='fadama_reports'),

    url(r'^fadama/message/$', fadama.MessageView.as_view(), name='fadama_new_message'),
    url(r'^fadama/debug/frombene/$', fadama.msg_from_bene),

    url(r'^fadama/api/main/$', fadama.api_main),
    url(r'^fadama/api/detail/$', fadama.api_detail),
)

