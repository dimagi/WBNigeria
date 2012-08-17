import datetime

from django.contrib.auth.models import User

from alerts.models import Notification, NotificationType, NotificationVisibility

from aremind.apps.dashboard.utils.fadama import load_reports, facilities_by_id


REPORT_TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'  # 'timestamp' column of a report
NOTIFICATION_DATE_FORMAT = '%d %B %Y'
PERIOD_BEFORE_NOTIFICATION = datetime.timedelta(days=2)


class IdleFacilityNotificationType(NotificationType):
    """Describes users to notify when a facility has been idle."""
    escalation_levels = ['everyone']

    def users_for_escalation_level(self, esc_level):
        return User.objects.all()

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return 'Everyone'


def trigger_notifications():
    """
    Generates Notifications for facilities which haven't sent in any reports 
    for more than PERIOD_BEFORE_NOTIFICATION days.

    Notifications for each facility are generated according to the following 
    rules:

        1) If no recent report exists from the facility and no Notification 
        exists for the facility, a Notification object is created for the
        facility. Newly-generated Notifications are not saved; this is the job
        of the caller.

        2) If no recent report exists from the facility but a Notification 
        already exists, that Notification is updated and saved to ensure that 
        it has the date of the last report.

        3) If a recent report exists from the facility, all related
        Notification and NotificationType objects are deleted.
            
    This method should be invoked by the trigger_alerts management command, 
    which should be run periodically as through a cron job or Celery.
    """ 
    def _get_uid(facility):
        """A unique way to identify a facility's notifications."""
        return 'facility_{0}_idle'.format(str(facility['id']))

    def _get_notification_text(facility, last_heard):
        """Message to the user when a facility has been idle recently."""
        text = "No new reports have been received from {0}".format(facility['name'])
        if not last_heard:
            text += " ever."
        else:
            text += " since {0}.".format(last_heard.strftime(NOTIFICATION_DATE_FORMAT))
        return text

    def _create_or_update_notification(facility, last_heard):
        """
        Creates a new idle Notification for the facility if one does not exist,
        or updates the existing Notification to ensure it has the most recent
        last_heard date.
        """
        uid = _get_uid(facility)
        try:
            existing = Notification.objects.get(alert_type=alert_type, uid=uid)

        # Create a new Notification.
        except Notification.DoesNotExist: 
            text = _get_notification_text(facility, last_heard)
            new = Notification(alert_type=alert_type, uid=uid, text=text)
            return new
        # This should not happen.
        except Notification.MultipleObjectsReturned: 
            raise
        # Update existing Notification with most recent last_heard date.
        else: 
            text = _get_notification_text(facility, last_heard)
            existing.text = text
            existing.save()
            return existing

    def _delete_existing_notification(facility):
        """Deletes any existing idle Notifications for the facility."""
        uid = _get_uid(facility)
        existing_notifs = Notification.objects.filter(alert_type=alert_type, uid=uid)
        ids = existing_notifs.values_list('id', flat=True)
        existing_visibility = NotificationVisibility.objects.filter(notif__id__in=ids)
        existing_notifs.delete()
        existing_visibility.delete()

    
    alert_type = 'aremind.notifications.idle_facilities.IdleFacilityNotificationType'
    facilities = facilities_by_id()  # Loads example data.
    reports = load_reports()  # Loads example data.
    now = datetime.datetime.now()

    # Map facility id to most recent report dates.
    recent_reports = dict(zip(facilities.keys(), [None for f in facilities.keys()])) 
    for report in reports:
        facility = report['facility']
        try:
            timestamp = datetime.datetime.strptime(report['timestamp'], REPORT_TIMESTAMP_FORMAT)
        except ValueError: # Skip reports with bad date format.
            continue
        if recent_reports[facility] == None or timestamp > recent_reports[facility]:
            recent_reports[facility] = timestamp
    
    # Create, update, or delete Notifications for each facility.
    for facility_id in recent_reports.keys():
        last_heard = recent_reports[facility_id]
        facility = facilities[facility_id]
        if not last_heard or now - last_heard > PERIOD_BEFORE_NOTIFICATION:
            yield  _create_or_update_notification(facility, last_heard)
        else:
            _delete_existing_notification(facility)
