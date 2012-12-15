from django.conf.urls.defaults import *

from aremind.apps.dashboard.views import fadama
from aremind.apps.dashboard.views import pbf
import aremind.apps.dashboard.views as shared

urlpatterns = patterns('',
    url(r'^$', shared.landing),

    url(r'^pbf/$', pbf.DashboardView.as_view(), name='pbf_dashboard'),
    url(r'^pbf/reports/$', pbf.ReportView.as_view(), name='pbf_reports'),

    url(r'^pbf/api/main/$', pbf.APIMainView.as_view(), name='pbf_api_main'),
    url(r'^pbf/api/detail/$', pbf.APIDetailView.as_view(), name='pbf_api_detail'),

    url(r'^fadama/$', fadama.DashboardView.as_view(), name='fadama_dashboard'),
    url(r'^fadama/reports/$', fadama.ReportView.as_view(), name='fadama_reports'),
    url(r'^fadama/reports/from/(?P<contact>\w+)/$', fadama.LogsForContactView.as_view(), name='fadama_contact_detail'),
    url(r'^fadama/report/(?P<id>\w+)/$', fadama.SingleReportView.as_view(), name='fadama_report_single'),

    url(r'^message/new/$', shared.MessageView.as_view(), name='new_message'),
    url(r'^message/del/$', shared.del_message, name='del_message'),
    url(r'^fadama/debug/frombene/$', fadama.msg_from_bene),

    url(r'^fadama/api/main/$', fadama.APIMainView.as_view(), name='fadama_api_main'),
    url(r'^fadama/api/detail/$', fadama.APIDetailView.as_view(), name='fadama_api_detail'),

    url(r'^dismiss/(?P<notification_id>\d+)/$', shared.DismissNotification.as_view(), name='fadama_dismiss_alert'),
)

