import json

from django.http import HttpResponse
from django.views import generic

from aremind.apps.dashboard.utils import pbf as utils
from aremind.apps.dashboard.utils import mixins
from aremind.apps.dashboard.utils import shared as u

class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/reports.html'

class SingleReportView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/pbf/single_log.html'

    def get_context_data(self, **kwargs):
        return {
            'logs': json.dumps(utils.log_single(int(kwargs['id']))),
            'taggable_contacts': json.dumps(u.get_taggable_contacts('pbf', u.get_user_state(self.request.user), self.request.user)),
        }



class APIDetailView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, user, **kwargs):
        state = self.get_user_state()
        return {
            'facilities': utils.get_facilities(),
            'monthly': utils.detail_stats(site),
            'taggable_contacts': u.get_taggable_contacts('pbf', state, user),
        }


class APIMainView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, **kwargs):
        return {
            'stats': utils.main_dashboard_stats(),
        }

