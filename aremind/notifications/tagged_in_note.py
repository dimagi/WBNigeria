from django.core.urlresolvers import reverse
from alerts.models import Notification, NotificationType, NotificationComment, user_name
from django.contrib.auth.models import User
from alerts.utils import trigger
import json
import logging

class TaggedInNoteNotificationType(NotificationType):
    escalation_levels = ['default']

    def users_for_escalation_level(self, esc_level):
        return User.objects.filter(id=json.loads(self.data)['user_id'])

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return esc_level


def mk_tagged_alert(user, comment):
    alert_type = 'aremind.notifications.tagged_in_note.TaggedInNoteNotificationType'

    notif = Notification(alert_type=alert_type)
    notif.uid = 'tagged_%s_%s' % (comment.id, user.username)
    notif.text = 'You have been tagged in a note by %s' % comment.author
    notif.url = reverse('fadama_report_single', kwargs={'id': comment.report.id})
    notif.data = json.dumps({'user_id': user.id})
    return notif

def trigger_alerts(comment):
    for c in comment.contact_tags.all():
        if c.user:
            notif = mk_tagged_alert(c.user, comment)
            msg = trigger(notif)
            logging.debug(msg)
