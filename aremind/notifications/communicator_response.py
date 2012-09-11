from alerts.models import Notification, NotificationType, NotificationComment, user_name
from django.contrib.auth.models import User
from alerts.utils import trigger
from apps.dashboard.models import ReportComment, FadamaReport
import json
import logging
from datetime import datetime
from django.conf import settings

class CommunicatorResponseNotificationType(NotificationType):
    escalation_levels = ['default']

    def users_for_escalation_level(self, esc_level):
        return User.objects.filter(id=json.loads(self.data)['user_id'])

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return esc_level


def mk_response_alert(user, report, reply, mode):
    alert_type = 'aremind.notifications.communicator_response.CommunicatorResponseNotificationType'

    notif = Notification(alert_type=alert_type)
    notif.uid = 'commreply_%s_%s' % (reply.id, user.username)
    if mode == 'sender':
        notif.text = 'A beneficiary has replied to an inquiry you sent them about a report'
    elif mode == 'tagged':
        notif.text = 'A beneficiary has replied to an inquiry about a report you were tagged on'
    elif mode == 'commenter':
        notif.text = 'A beneficiary has replied to an inquiry on a report that you\'ve left comments on'
    notif.url = None
    notif.data = json.dumps({'user_id': user.id})
    return notif

def trigger_alerts(report, response):
    report_activity = report.reportcomment_set.filter(
        date__gte=datetime.now() - settings.COMMUNICATOR_RESPONSE_WINDOW
    )

    inquiring_users = set()
    tagged_users = set()
    commenting_users = set()

    for c in report_activity:
        if c.comment_type == ReportComment.INQUIRY_TYPE:
            user_id = (json.loads(c.extra_info) if c.extra_info else {}).get('user_id')
            try:
                user = User.objects.get(id=user_id)
                inquiring_users.add(user)
            except User.DoesNotExist:
                pass

        tagged_users = tagged_users.union(ct.user for ct in c.contact_tags.all())
        #commenting_users.add() # figure out later

    def notifs():
        for u in inquiring_users:
            yield mk_response_alert(u, report, response, 'sender')
        for u in tagged_users - inquiring_users:
            yield mk_response_alert(u, report, response, 'tagged')
        for u in commenting_users - tagged_users - inquiring_users:
            yield mk_response_alert(u, report, response, 'commenter')
    for notif in notifs():
        msg = trigger(notif)
        logging.debug(msg)



