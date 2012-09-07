import json

from django.http import HttpResponse
from django.views import generic

from aremind.apps.dashboard.utils import pbf as utils
from aremind.apps.dashboard.utils import mixins


class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/reports.html'


class APIDetailView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, **kwargs):
        return {
            'facilities': utils.get_facilities(),
            'monthly': utils.detail_stats(site),
        }


class APIMainView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, **kwargs):
        return {
            'stats': utils.main_dashboard_stats(),
        }

