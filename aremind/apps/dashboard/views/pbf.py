import json

from django.http import HttpResponse
from django.views.generic import TemplateView

from aremind.apps.dashboard.utils import pbf as utils
from aremind.apps.dashboard.utils import mixins


class DashboardView(mixins.LoginMixin, TemplateView):
    template_name = 'dashboard/pbf/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, TemplateView):
    template_name = 'dashboard/pbf/reports.html'


def api_main(request):
    payload = {
        'stats': utils.main_dashboard_stats(),
    }
    return HttpResponse(json.dumps(payload), 'text/json')


def api_detail(request):
    _site = request.GET.get('site')
    site = int(_site) if _site else None

    payload = {
        'facilities': utils.FACILITIES,
        'monthly': utils.detail_stats(site),
    }
    return HttpResponse(json.dumps(payload), 'text/json')
