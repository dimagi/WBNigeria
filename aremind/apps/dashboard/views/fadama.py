import json

from django.http import HttpResponse
from django.views import generic

from aremind.apps.dashboard import forms
from aremind.apps.dashboard.models import ReportComment
from aremind.apps.dashboard.utils import fadama as utils
from aremind.apps.dashboard.utils import mixins


class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/reports.html'


class MessageView(generic.CreateView):
    def dispatch(self, request, *args, **kwargs):
        return super(MessageView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.ReportCommentForm(request.POST)

        if form.is_valid():
            comment = form.save()
            if comment.comment_type == ReportComment.INQUIRY_TYPE:
                # Send SMS to beneficiary
                utils.message_report_beneficiary(comment.report_id, comment.text)
            return HttpResponse(json.dumps(comment.json()),
                mimetype='application/json')

        return HttpResponse('', mimetype='application/json')


class APIDetailView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site):
        state = self.get_user_state()
        return {
            'facilities': [f for f in utils.FACILITIES if state is None or f['state'] == state],
            'monthly': utils.detail_stats(site, state),
        }


class APIMainView(mixins.LoginMixin, mixins.APIMixin, generic.View):
    def get_payload(self, site):
        return {
            'stats': utils.main_dashboard_stats(self.get_user_state()),
        }


def msg_from_bene(request):
    rc = ReportComment()
    rc.report_id = int(request.GET.get('id'))
    rc.comment_type = 'response'
    rc.author = '_bene'
    rc.text = request.GET.get('text')
    rc.save()
    return HttpResponse('ok', 'text/plain')
