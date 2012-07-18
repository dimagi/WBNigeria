import json

from django.http import HttpResponse
from django.views import generic

from aremind.apps.dashboard.utils import pbf as utils
from aremind.apps.dashboard.utils import mixins


class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/reports.html'


class APIDetailView(mixins.LoginMixin, generic.View):
    def get(self, request, *args, **kwargs):
        _site = request.GET.get('site')
        site = int(_site) if _site else None

        payload = {
            'facilities': utils.FACILITIES,
            'monthly': utils.detail_stats(site),
        }
        return HttpResponse(json.dumps(payload), 'text/json')


class APIMainView(mixins.LoginMixin, generic.View):
    def get(self, request, *args, **kwargs):
        payload = {
            'stats': utils.main_dashboard_stats(),
        }
        return HttpResponse(json.dumps(payload),
            mimetype='application/json')
