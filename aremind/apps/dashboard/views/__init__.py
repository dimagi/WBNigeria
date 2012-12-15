from django.http import HttpResponse
from django.shortcuts import render
from pbf import *
from fadama import *
from django.views import generic
from aremind.apps.dashboard import forms
from aremind.apps.dashboard.utils import fadama as utils
from aremind.notifications.tagged_in_note import trigger_alerts
from aremind.apps.dashboard.models import PBFReport, FadamaReport, ReportComment
from django.contrib.auth.decorators import login_required
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


