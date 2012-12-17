import json

from django.http import HttpResponse
from django.views import generic
from django.contrib.auth.decorators import login_required

from alerts.models import NotificationVisibility

from aremind.apps.dashboard import forms
from aremind.apps.dashboard.models import FadamaReport, ReportComment, ReportCommentView
from aremind.apps.dashboard.utils import fadama as utils
from aremind.apps.dashboard.utils import mixins
from aremind.apps.dashboard.utils import shared as u
from aremind.notifications.tagged_in_note import trigger_alerts


class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/reports.html'

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        context['fadama_communicator_prefix'] = utils.communicator_prefix()
        return context


class LogsForContactView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/logs_for_contact.html'

    def get_context_data(self, **kwargs):
        return {
            'logs': json.dumps(utils.logs_for_contact(kwargs['contact'])),
            'taggable_contacts': json.dumps(u.get_taggable_contacts('fadama', u.get_user_state(self.request.user), self.request.user)),
            'fadama_communicator_prefix': utils.communicator_prefix(),
        }


class SingleReportView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/single_log.html'

    def get_context_data(self, **kwargs):
        return {
            'logs': json.dumps(utils.log_single(int(kwargs['id']))),
            'taggable_contacts': json.dumps(u.get_taggable_contacts('fadama', u.get_user_state(self.request.user), self.request.user)),
            'fadama_communicator_prefix': utils.communicator_prefix(),
        }


class APIDetailView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, user, **kwargs):
        state = self.get_user_state()
        return {
            'facilities': [f for f in utils.get_facilities() if state is None or f['state'] == state],
            'monthly': utils.detail_stats(site, self.request.user, state),
            'taggable_contacts': u.get_taggable_contacts('fadama', state, user),
        }


class APIMainView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site, **kwargs):
        return {
            'stats': utils.main_dashboard_stats(user=self.request.user, state=self.get_user_state()),
        }


def msg_from_bene(request):
    rc = ReportComment()
    rc.report = FadamaReport.objects.get(id=int(request.GET.get('id')))
    rc.comment_type = 'response'
    rc.author = ReportComment.FROM_BENEFICIARY
    rc.text = request.GET.get('text')
    rc.save()
    return HttpResponse('ok', 'text/plain')
