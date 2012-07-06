from django.conf import settings
from django.conf.urls.defaults import *

from aremind.apps.dashboard.views import pbf
from aremind.apps.dashboard.views import fadama
from aremind.apps.dashboard.views import load_test_data

urlpatterns = patterns('',
    url(r'^pbf/$', pbf.dashboard, name='pbf_dashboard'),
    url(r'^pbf/reports/$', pbf.reports, name='pbf_reports'),
    url(r'^pbf/reports/(?P<pk>\d+)/$', pbf.site_detail, name='pbf_site_detail'),

    url(r'^pbf/api/main/$', pbf.api_main),

    url(r'^fadama/$', fadama.dashboard, name='fadama_dashboard'),
    url(r'^fadama/reports/$', fadama.reports, name='fadama_reports'),
    url(r'^fadama/reports/(?P<pk>\d+)/$', fadama.site_detail, name='fadama_site_detail'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^load/$', load_test_data, name='load_test_data')
    )
