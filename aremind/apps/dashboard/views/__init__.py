from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from aremind.apps.dashboard import forms
from aremind.apps.dashboard.utils import fadama as utils
from aremind.apps.dashboard.utils import mixins
from aremind.notifications.tagged_in_note import trigger_alerts
from aremind.apps.dashboard.models import PBFReport, FadamaReport, ReportComment, ReportCommentView
from aremind.apps.dashboard.views import pbf
from aremind.apps.dashboard.views import fadama
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

def landing(request):
    return render(request, 'dashboard/base.html', {'shownav': True})

class MessageView(generic.CreateView):
    http_method_names = ['post', ]

    def post(self, request, *args, **kwargs):
        form = forms.ReportCommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            u = request.user
            comment.author = '%s %s' % (u.first_name, u.last_name)
            comment.author_user = u
            comment.save()
            form.save_m2m()
            if comment.comment_type == ReportComment.INQUIRY_TYPE:
                comment.extra_info = json.dumps({'user_id': u.id})
                comment.save()
                # Send SMS to beneficiary
                utils.message_report_beneficiary(comment.report, comment.text)
            if comment.comment_type == ReportComment.NOTE_TYPE:
                # Generate notifications for tagged users.
                trigger_alerts(comment)
            # Mark the comment as viewed by the user.
            ReportCommentView.objects.create(user=u, report_comment=comment)
            return HttpResponse(json.dumps(comment.json()),
                mimetype='application/json')

        return HttpResponse('', mimetype='application/json')

@login_required
def del_message(request):
    id = int(request.POST.get('id'))
    ReportComment.objects.get(id=id).delete()
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
@require_POST
def view_comments(request):
    "Mark comments as read by the current user by creating ReportCommentViews."
    comment_ids = json.loads(request.raw_post_data)
    comments = ReportComment.objects.filter(id__in=comment_ids)
    for c in comments:
        ReportCommentView.objects.get_or_create(user=request.user, report_comment=c)
    viewed_ids = list(comments.values_list('id', flat=True))
    return HttpResponse(json.dumps(viewed_ids), 'text/plain')


class SupvervisorView(mixins.AuditMixin, generic.TemplateView):

    dashboard = None

    def get_template_names(self):
        return ['dashboard/%s/supervisor.html' % self.dashboard, 'dashboard/supervisor.html' ]

    def get_context_data(self, **kwargs):
        context = super(SupvervisorView, self).get_context_data(**kwargs)
        context['actions'] = self.get_user_actions()
        context['national_user'] = (not self.contact.location_id) or (self.contact.location.type.slug != 'state')
        return context


class AllAlerts(generic.TemplateView):
    template_name = 'dashboard/all_alerts.html'

    def get_context_data(self, program, **kwargs):
        return {
            'program': program,
        }
