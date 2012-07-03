from django.conf.urls.defaults import *

from aremind.apps.dashboard.views import pbf
from aremind.apps.dashboard.views import fadama

urlpatterns = patterns('',
    url(r'^pbf/$', pbf.dashboard, name='pbf_dashboard'),
    url(r'^pbf/reports/$', pbf.reports, name='pbf_reports'),

    url(r'^fadama/$', fadama.dashboard, name='fadama_dashboard'),
    url(r'^fadama/reports/$', fadama.reports, name='fadama_reports'),
    url(r'^fadama/reports/(?P<pk>\d+)/$', fadama.report_detail, name='fadama_report_detail'),
)
