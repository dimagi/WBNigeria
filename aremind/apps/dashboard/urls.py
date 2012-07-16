from django.conf import settings
from django.conf.urls.defaults import *

from aremind.apps.dashboard.views import fadama
from aremind.apps.dashboard.views import pbf

urlpatterns = patterns('',
    url(r'^pbf/$', pbf.dashboard, name='pbf_dashboard'),
    url(r'^pbf/reports/$', pbf.reports, name='pbf_reports'),

    url(r'^pbf/api/main/$', pbf.api_main),
    url(r'^pbf/api/detail/$', pbf.api_detail),

    url(r'^fadama/$', fadama.dashboard, name='fadama_dashboard'),
    url(r'^fadama/reports/$', fadama.reports, name='fadama_reports'),

    url(r'^fadama/message/$', fadama.new_message),
    url(r'^fadama/debug/frombene/$', fadama.msg_from_bene),

    url(r'^fadama/api/main/$', fadama.api_main),
    url(r'^fadama/api/detail/$', fadama.api_detail),
)

