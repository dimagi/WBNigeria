import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from aremind.apps.dashboard import forms
from aremind.apps.dashboard.models import ReportComment
from aremind.apps.dashboard.utils import fadama as utils
from aremind.apps.dashboard.utils import mixins


class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/reports.html'


class MessageView(generic.CreateView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(MessageView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = forms.ReportCommentForm(request.POST)

        if form.is_valid():
            rc = form.save()
            return HttpResponse(json.dumps(rc.json()),
                mimetype='application/json')

        return HttpResponse('', mimetype='application/json')


def api_detail(request):
    _site = request.GET.get('site')
    site = int(_site) if _site else None

    payload = {
        'facilities': [f for f in utils.FACILITIES if f['state'] == utils.user_state()],
        'monthly': utils.detail_stats(site),
    }
    return HttpResponse(json.dumps(payload), 'text/json')


def api_main(request):
    payload = {
        'stats': utils.main_dashboard_stats(),
    }
    return HttpResponse(json.dumps(payload), 'text/json')


def msg_from_bene(request):
    rc = ReportComment()
    rc.report_id = int(request.GET.get('id'))
    rc.comment_type = 'response'
    rc.author = '_bene'
    rc.text = request.GET.get('text')
    rc.save()
    return HttpResponse('ok', 'text/plain')
