import datetime

from django.contrib.auth.models import User

from alerts.models import Notification, NotificationType, NotificationVisibility


class ReportCommentTagNotificationType(NotificationType):
    """
    Dummy NotificationType for ReportComment tag Notifications.  We will 
    handle the notification of users.
    """
    escalation_levels = ['default']

    def users_for_escalation_level(self, esc_level):
        return User.objects.none()

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return None


def create_comment_tag_notification(comment):
    """
    Creates a Notification object for the given comment that is visible only
    to the tagged users.

    This method should be invoked when a comment is created.
    """
    def _get_uid(comment):
        """A unique way to identify a comment's tag notifications."""
        return 'report_comment_tag_{0}'.format(str(comment.id))

    def _get_text(comment):
        """Message to users who have been tagged in this comment."""
        return "{0} tagged you in a report comment on {1}.".format(
                comment.author, comment.date.strftime('%Y-%m-%d %H:%M:%s'))

    # The users for whom to create a notification.
    users = comment.contact_tags.exclude(user__isnull=True).values_list(
            'user', flat=True)
    if not users:
        return  # Do not create a Notification if no users are tagged.

    notif_data = {
        'uid': _get_uid(comment),
        'text': _get_text(comment),
        'alert_type': 'aremind.notifications.report_comment_tags.ReportCommentTagNotificationType',
    }
    if Notification.objects.filter(uid=notif_data['uid']).exists():
        return  # Do not create a notification for this comment if one already exists.
    notif = Notification(**notif_data)
    notif.initialize()

    for contact in comment.contact_tags.filter(user__isnull=False):
        nv_data = {
            'notif': notif,
            'user': contact.user,
            'esc_level': notif.initial_escalation_level,
        }
        NotificationVisibility.objects.get_or_create(**nv_data)
