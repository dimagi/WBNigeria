import json

from django.http import HttpResponse
from django.views import generic
from django.contrib.auth.decorators import login_required

from alerts.models import NotificationVisibility

from aremind.apps.dashboard import forms
from aremind.apps.dashboard.models import ReportComment
from aremind.apps.dashboard.utils import fadama as utils
from aremind.apps.dashboard.utils import mixins

class DashboardView(mixins.LoginMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/dashboard.html'


class ReportView(mixins.LoginMixin, mixins.ReportMixin, generic.TemplateView):
    template_name = 'dashboard/fadama/reports.html'

    def get_context_data(self, **kwargs):
        context = super(ReportView, self).get_context_data(**kwargs)
        context['fadama_communicator_prefix'] = utils.communicator_prefix()
        return context


class MessageView(generic.CreateView):
    http_method_names = ['post', ]

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


class DismissNotification(mixins.LoginMixin, generic.View):
    "Mark a Notification as viewed by removing the NotificationVisibility."

    http_method_names = ['post', 'delete', ]

    def delete(self, request, *args, **kwargs):
        "Delete the NotificationVisibility for this user/notification pair."
        notification_id = kwargs['notification_id']
        user = self.request.user
        visibility = user.alerts_visible.filter(notif__id=notification_id)
        if visibility.exists():
            visibility.delete()
            status = 200
        else:
            status = 204        
        return HttpResponse('', status=status, mimetype='application/json')

    def post(self, request, *args, **kwargs):
        "Browsers don't support HTTP DELETE so call the delete from a POST."
        return self.delete(request, *args, **kwargs)


@login_required
def del_message(request):
    id = int(request.POST.get('id'))
    ReportComment.objects.get(id=id).delete()
    return HttpResponse('ok', 'text/plain')
