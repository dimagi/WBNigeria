import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from rapidsms.messages import OutgoingMessage

from alerts.models import Notification, NotificationType, NotificationVisibility

from threadless_router.router import Router as ThreadlessRouter

from aremind.apps.dashboard.models import FadamaReport, PBFReport, ReportComment


class DigestNotificationType(NotificationType):
    """Describes users who should receive activity digests."""
    escalation_levels = ['web_users']
    notify_sms = False  # We'll handle this manually through the post-save hook.

    def users_for_escalation_level(self, esc_level):
        raise NotImplemented('Must be defined in subclass.')

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return esc_level


class DigestNotification(object):
    """Generate an activity digest for the previous week."""

    @property
    def slug(self):
        raise NotImplemented('Must be defined in subclass.')

    @property
    def alert_type(self):
        raise NotImplemented('Must be defined in subclass.')

    @property
    def report_type(self):
        raise NotImplemented('Must be defined in subclass.')

    @property
    def comment_field(self):
        raise NotImplemented('Must be defined in subclass.')

    def __call__(self):
        today = datetime.datetime.now()
        today = datetime.datetime(today.year, today.month, today.day)  # Midnight.
        self.this_week = self._get_monday(today)
        self.last_week = self.this_week - datetime.timedelta(days=7)
        uid = self.get_uid()

        try:
            notif = Notification.objects.get(alert_type=self.alert_type, uid=uid)
        except Notification.DoesNotExist:
            text = self.get_text()
            # Don't save; that is done by the alerts framework.
            notif = Notification(alert_type=self.alert_type, uid=uid, text=text)

        yield notif

    def _get_monday(self, date=None):
        days_since_monday = date.weekday()  # Monday is 0.
        if days_since_monday:
            return date - datetime.timedelta(days=days_since_monday)
        return date

    def get_comments(self):
        """Retrieves all comments for the previous full week (Mon-Sun)."""
        dateQ = Q(date__gte=self.last_week, date__lt=self.this_week)
        kwargs = {self.comment_field + '__isnull': False}
        return ReportComment.objects.filter(dateQ, **kwargs)

    def get_reports(self):
        """Retrieves all reports for the previous full week (Mon-Sun)."""
        dateQ = Q(timestamp__gte=self.last_week, timestamp__lt=self.this_week)
        return self.report_type.objects.filter(dateQ)

    def get_text(self):
        last_week_str = self.last_week.strftime('%b %d')
        this_week_str = self.this_week.strftime('%b %d')
        text = '{0} digest for {1}-{2}: \n'.format(self.slug, last_week_str, this_week_str)

        reports = self.get_reports()
        comments = self.get_comments()
        data = self.summarize(reports, comments)

        summary = '\n'.join([': '.join((key, str(value))) for key, value in data.items()])
        text += summary
        return text

    def get_uid(self):
        week_str = self.this_week.strftime('%Y%m%d')
        return '{0}_digest_{1}'.format(self.slug, week_str)

    def summarize(self, reports, comments):
        """Summary should be <=105 characters to stay in one message."""
        data = {}
        data['Reports'] = len(reports)
        data['Notes'] = len(comments.filter(comment_type=ReportComment.NOTE_TYPE))
        data['Inquiries'] = len(comments.filter(comment_type=ReportComment.INQUIRY_TYPE))
        data['Responses'] = len(comments.filter(comment_type=ReportComment.REPLY_TYPE))
        return data


@receiver(post_save, sender=NotificationVisibility, '1y2c26anwcmcm')
def send_activity_digest_sms(sender, instance, created, **kwargs):
    """
    Uses threadless_router to send the activity digest via SMS to
    all available contacts associated with the user. This will happen only
    once when the NotificationVisibility object is created.

    The default SMS handling provided by rapidsms-alerts is not compatible
    with threadless router.
    """
    alert_types = [PBFDigestNotification.alert_type, FadamaDigestNotification.alert_type]
    sent = False
    if created and instance.notif.alert_type in alert_types:
        notification = instance.notif
        contacts = instance.user.contact_set.all()
        for contact in contacts:
            connection = contact.default_connection
            if connection:
                backend = connection.backend
                message = OutgoingMessage(connection, notification.text)
                router = ThreadlessRouter()
                response = router.outgoing(message)
                sent = True
    if sent:
        # Don't show this notification on the dashboard as we've already sent
        # it as a text message.
        instance.delete()


############################################
# Activity digest for Fadama administrators.
############################################


class FadamaDigestNotificationType(DigestNotificationType):

    def users_for_escalation_level(self, esc_level):
        return User.objects.filter(user_permissions__codename='fadama_view')\
                           .exclude(user_permissions__codename='pbf_view')


class FadamaDigestNotification(DigestNotification):
    slug = 'Fadama'
    alert_type = 'aremind.notifications.digests.FadamaDigestNotificationType'
    report_type = FadamaReport
    comment_field = 'fadama_report'


fadama_digest_notifications = FadamaDigestNotification()


#########################################
# Activity digest for PBF administrators.
#########################################


class PBFDigestNotificationType(DigestNotificationType):

    def users_for_escalation_level(self, esc_level):
        return User.objects.filter(user_permissions__codename='pbf_view')\
                           .exclude(user_permissions__codename='fadama_view')


class PBFDigestNotification(DigestNotification):
    slug = 'PBF'
    alert_type = 'aremind.notifications.digests.PBFDigestNotificationType'
    report_type = PBFReport
    comment_field = 'pbf_report'


pbf_digest_notifications = PBFDigestNotification()
