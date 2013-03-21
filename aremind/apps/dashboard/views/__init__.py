from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
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

from apps.utils.functional import map_reduce
from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend, Connection
from rapidsms.messages.outgoing import OutgoingMessage
from apps.dashboard.utils.shared import network_for_number
from django.conf import settings
from apps.reimbursement.models import ReimbursementLog, get_backend_name
import math
from datetime import datetime, date
from threadless_router.router import Router


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

def disp_number(number):
    disp_number = number
    if disp_number.startswith('+'):
        disp_number = disp_number[1:]
    if disp_number.startswith('234'):
        disp_number = '0' + disp_number[3:]
    return disp_number

def reimbursement(request):
    messages = Message.objects.filter(direction='I').select_related()
    by_number = map_reduce(messages, lambda m: [(m.connection.identity, m)], lambda v: sorted(v, key=lambda e: e.date))
    reimbursements = map_reduce(ReimbursementLog.objects.all(), lambda e: [(e.phone, e.amount)], sum)

    def mk_entry(number, messages):
        entry = {
            'number': number,
            'disp_number': disp_number(number),
            'network': network_for_number(number),
            'total_reimbursed': reimbursements.get(number, 0),
            'most_recent': messages[-1].date.strftime('%Y-%m-%d %H:%M:%S'),
        }
        if not entry['network']:
            return None

        cost_per_sms = settings.REIMBURSEMENT_RATES[entry['network']]

        entry['total_spent'] = cost_per_sms * len(messages)

        owed = entry['total_spent'] - entry['total_reimbursed']
        entry['earliest_unreimbursed'] = None
        if owed > 0:
            num_unreimbursed = int(math.ceil(owed / float(cost_per_sms)))
            entry['earliest_unreimbursed'] = messages[-num_unreimbursed].date.strftime('%Y-%m-%d %H:%M:%S')

        return entry

    def sort_key(entry):
        owed = entry['total_spent'] - entry['total_reimbursed']
        if owed > 0:
            return (False, entry['earliest_unreimbursed'])
        else:
            return (True, entry['number'])

    data = sorted(filter(None, [mk_entry(k, v) for k, v in by_number.iteritems()]), key=sort_key)
    return render(request, 'dashboard/reimbursement.html', {
            'data': json.dumps(data),
        })

def reimbursement_detail(request, number):
    reimbursements = ReimbursementLog.objects.filter(phone=number).order_by('-reimbursed_on')
    num_messages = Message.objects.filter(connection__identity=number, direction='I').count()
    owed = settings.REIMBURSEMENT_RATES[network_for_number(number)] * num_messages - sum([r.amount for r in reimbursements])

    from django import forms
    from django.contrib.admin.widgets import AdminDateWidget
    class ReimbursementForm(forms.Form):
        amount = forms.IntegerField()
        when = forms.DateField(widget=AdminDateWidget, required=False)

        def clean_amount(self):
            data = self.cleaned_data['amount']
            if data <= 0:
                raise forms.ValidationError('can\'t be 0 or negative')
            return data

    if request.method == 'POST':
        form = ReimbursementForm(request.POST)
        if form.is_valid():
            entry_date = form.cleaned_data['when']
            entry = ReimbursementLog(
                phone=number,
                amount=form.cleaned_data['amount'],
                reimbursed_on=datetime.now() if (not entry_date or entry_date == date.today()) else entry_date,
            )
            entry.save()

            #import pdb;pdb.set_trace()
            network_name = network_for_number(number)
            backend_name = get_backend_name(network_name)
            backend, _ = Backend.objects.get_or_create(name=backend_name)
            try:
                conn = Connection.objects.get(identity=number, backend=backend)
            except Exception:
                #log somewhere?
                pass
            else:
                notice = OutgoingMessage(connection=conn, template=settings.REIMBURSEMENT_NOTICE)
                router = Router()
                router.outgoing(notice)

            return HttpResponseRedirect('/dashboard/reimbursement/')
    else:
        form = ReimbursementForm()

    return render(request, 'dashboard/reimbursement_detail.html', {
            'number': disp_number(number),
            'network': network_for_number(number),
            'owed': owed,
            'over': owed < 0,
            'over_amt': -owed,
            'history': reimbursements,
            'form': form,
        })

def reimbursement_delete(request):
    log = ReimbursementLog.objects.get(id=request.POST.get('id'))
    phone = log.phone
    log.delete()
    return HttpResponseRedirect(reverse(reimbursement_detail, kwargs={'number': phone}))
