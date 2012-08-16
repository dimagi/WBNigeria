import datetime

from django.contrib.auth.models import User

from alerts.models import Notification, NotificationType
from alerts import utils

from aremind.apps.dashboard.utils.fadama import load_reports, facilities_by_id


REPORT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
NOTIFICATION_DATE_FORMAT = '%d %B %Y'

# We generate a notification when no reports have been received from 
# a particular facility for more than a certain number of days.
DAYS_BEFORE_NOTIFICATION = datetime.timedelta(days=7)


class IdleFacilityNotificationType(NotificationType):
    """
    Describes the users who should be notified when no recent reports have 
    been received from a particular facility.
    """
    escalation_levels = ['everyone']

    def users_for_escalation_level(self, esc_level):
        return User.objects.all()

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return 'Everyone'


def trigger_idle_facility_notifications():
    """
    Creates Notifications for facilities which haven't sent in any reports for
    more than DAYS_BEFORE_NOTIFICATION days.

    This method must be run periodically, as through a cron job or Celery.  
    Notification objects are persistent until they are resolved. If a recent
    report has been received from a facility, then open idle notifications are
    resolved.
    """

    def _get_uid(facility):
        """A unique way to identify idle notifications for a facility."""
        return 'facility_{0}_idle'.format(str(facility['id']))

    def _create_place_notification(facility, last_heard):
        """
        Creates a Notification object alerting how long it has been since 
        hearing from the facility.
        """
        alert_type = 'aremind.notifications.IdleFacilityNotificationType'
        notif = Notification(alert_type=alert_type)
        notif.uid = _get_uid(facility)
        notif.text = ("No new reports have been received from {0}").format(facility['name'])
        if not last_heard:
            notif.text += " ever."
        else:
            notif.text += "since {0}.".format(last_heard.strftime(NOTIFICATION_DATE_FORMAT))
        return notif

    def _resolve_open_notifications(facility, last_heard):
        """Resolves any open idle notifications for this facility."""
        uid = _get_uid(facility)
        notifs = Notification.objects.filter(uid=uid, is_open=True)
        for notif in notifs: 
            notif.resolve()
            notif.save()
            text = ("This issue was automatically resolved because a "
                    "notification was received at {0}.").format(
                    last_heard.strftime(NOTIFICATION_DATE_FORMAT))
            utils.add_user_comment(alert=notif, user=None, text=text)   


    facilities = facilities_by_id()  # Loads example data.
    reports = load_reports()  # Loads example data.
    now = datetime.datetime.now()

    # Map facility id to most recent report dates.
    recent_reports = dict(zip(facilities.keys(), [None for f in facilities.keys()])) 
    for report in reports:
        facility = report['facility']
        try:
            timestamp = datetime.datetime.strptime(report['timestamp'], REPORT_DATE_FORMAT)
        except ValueError: # Skip reports with bad date format.
            continue
        if recent_reports[facility] == None or timestamp > recent_reports[facility]:
            recent_reports[facility] = timestamp
    
    # Generate a notification for any facility that hasn't received a report 
    # recently, and resolve open notifications for facilities that are no 
    # longer idle.
    for facility in recent_reports:
        last_heard = recent_reports[facility]
        if not last_heard or now - last_heard > DAYS_BEFORE_NOTIFICATION:
            yield _create_place_notification(facilities[facility], last_heard)
        else:
            _resolve_open_notifications(facilities[facility], last_heard)
