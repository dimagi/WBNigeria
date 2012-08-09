import datetime
import random

from django.contrib.auth.models import User

from alerts.models import Notification, NotificationType

from aremind.apps.dashboard.utils.fadama import load_reports, facilities_by_id


REPORT_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'
NOTIFICATION_DATE_FORMAT = '%d %B, %Y'

# We generate a notification when no reports have been received from 
# a particular facility for more than a certain number of days.
DAYS_BEFORE_NOTIFICATION = datetime.timedelta(days=1)


class ReportNotificationType(NotificationType):
    escalation_levels = ['everyone']

    def users_for_escalation_level(self, esc_level):
        return User.objects.all()

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return 'Everyone'


def trigger_place_notifications():
    """
    Creates Notifications for facilities which haven't been heard from in
    DAYS_BEFORE_NOTIFICATION days.

    This method must be run periodically, as through a cron job or Celery.  
    Notification objects are persistent until they are resolved.
    """

    def _create_place_notification(facility, last_heard=None):
        """
        Creates a Notification object alerting how long it has been since 
        hearing from the facility.
        """
        alert_type = 'aremind.notifications.ReportNotificationType'
        notif = Notification(alert_type=alert_type)
        notif.uid = random.randint(1,10000000000000)
        if last_heard:
            notif.text = ("No new reports have been received from {0} since "
                    "{1}.").format(facility['name'], last_heard.strftime(NOTIFICATION_DATE_FORMAT))
        else:
            notif.text = ("No new reports have been received recently from "
                    "{0}.").format(facility['name'])
        return notif

    reports = load_reports()  # Loads example data.
    facilities = facilities_by_id()  # Loads example data.
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
    
    # Generate a notification for any facility that hasn't received
    # a report recently.
    for facility in recent_reports:
        print "{0}: {1}".format(facilities[facility]['name'], recent_reports[facility])
        if not recent_reports[facility] or now - recent_reports[facility] > DAYS_BEFORE_NOTIFICATION:
            yield _create_place_notification(facilities[facility], recent_reports[facility])

