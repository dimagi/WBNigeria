import datetime

from django.contrib.auth.models import User

from rapidsms.contrib.locations.models import Location

from alerts.models import Notification, NotificationType, NotificationVisibility

from aremind.apps.dashboard.models import FadamaReport, PBFReport
from aremind.apps.dashboard.utils.shared import get_users_by_program


class IdleFacilitiesNotificationType(NotificationType):
    """Describes users to notify when a facility has been idle."""
    escalation_levels = ['web_users']

    def users_for_escalation_level(self, esc_level):
        raise NotImplemented('Must be defined in subclass.')

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return esc_level


class IdleFacilitiesNotification(object):
    """
    Generates Notifications for facilities which haven't sent in any reports
    for more than the specified number of days (default 15). Notifications for
    each facility are generated according to the following rules:

        1) If no recent report exists from the facility and no Notification
        exists for the facility, a Notification object is created for the
        facility. Newly-generated Notifications are not saved; this is the job
        of the caller.

        2) If no recent report exists from the facility but a Notification
        already exists, that Notification is updated and saved to ensure that
        it has the date of the last report.

        3) If a recent report exists from the facility, all related
        Notification and NotificationType objects are deleted.
    """
    NOTIFICATION_DATE_FORMAT = '%d %B %Y'

    def __init__(self, slug, report_type, locationtype_slugs, alert_type, period_before_notification=None):
        self.slug = slug
        self.report_type = report_type
        self.locationtype_slugs = locationtype_slugs
        self.alert_type = alert_type
        self.period_before_notification = period_before_notification or datetime.timedelta(days=15)

    def get_uid(self, facility_id):
        """A unique way to identify a facility's notifications."""
        return '{0}_facility_{1}_idle'.format(self.slug, facility_id)

    def get_notification_text(self, facility_name, last_heard):
        """Message to the user when a facility has been idle recently."""
        text = 'No new reports have been received from <strong>{0}</strong>'.format(facility_name)
        if not last_heard:
            text += ' <strong>ever</strong>.'
        else:
            text += ' since <strong>{0}</strong>.'.format(last_heard.strftime(self.NOTIFICATION_DATE_FORMAT))
        return text

    def create_or_update_notification(self, facility_id, facility_name, last_heard):
        """
        Creates a new idle Notification for the facility if one does not exist,
        or updates the existing Notification to ensure it has the most recent
        last_heard date.
        """
        uid = self.get_uid(facility_id)
        text = self.get_notification_text(facility_name, last_heard)
        try:
            existing = Notification.objects.get(alert_type=self.alert_type, uid=uid)
        except Notification.DoesNotExist:
            # Create a new Notification - no need to save as that is done by
            # the alerts framework
            new = Notification(alert_type=self.alert_type, uid=uid, text=text)
            return new
        else:
            # Update existing Notification with most recent last_heard date.
            existing.text = text
            existing.save()
            return existing

    def delete_existing_notification(self, facility_id):
        """Deletes any existing idle Notifications for the facility."""
        uid = self.get_uid(facility_id)
        existing_notifs = Notification.objects.filter(alert_type=self.alert_type, uid=uid)
        ids = existing_notifs.values_list('id', flat=True)
        existing_visibility = NotificationVisibility.objects.filter(notif__id__in=ids)
        existing_notifs.delete()
        existing_visibility.delete()

    def get_facilities(self):
        """Maps {id: name}."""
        return dict(Location.objects.filter(type__slug__in=self.locationtype_slugs).values_list('id', 'name'))

    def get_reports(self):
        return self.report_type.objects.values('site', 'timestamp')

    def __call__(self, *args, **kwargs):
        facilities = self.get_facilities()
        reports = self.get_reports()
        now = datetime.datetime.now()

        # Map facility id to most recent report dates.
        count = len(facilities.keys())
        recent_reports = dict(zip(facilities.keys(), [None for i in range(count)]))
        for report in reports:
            fid = report['site']
            if (recent_reports[fid] == None) or (report['timestamp'] > recent_reports[fid]):
                recent_reports[fid] = report['timestamp']

        # Create, update, or delete Notifications for each facility.
        for fid in recent_reports.keys():
            last_heard = recent_reports[fid]
            if not last_heard or now - last_heard > self.period_before_notification:
                fname = facilities[fid]
                yield self.create_or_update_notification(fid, fname, last_heard)
            else:
                self.delete_existing_notification(fid)


#########################################################
# Idle facilities notification for Fadama administrators.
#########################################################


class FadamaIdleFacilitiesNotificationType(IdleFacilitiesNotificationType):

    def users_for_escalation_level(self, esc_level):
        return get_users_by_program('fadama')


fadama_idle_facilities = IdleFacilitiesNotification('fadama', FadamaReport, ['fca', 'fug'], 'aremind.notifications.idle_facilities.FadamaIdleFacilitiesNotificationType')


######################################################
# Idle facilities notification for PBF administrators.
######################################################


class PBFIdleFacilitiesNotificationType(IdleFacilitiesNotificationType):

    def users_for_escalation_level(self, esc_level):
        return get_users_by_program('pbf')


pbf_idle_facilities = IdleFacilitiesNotification('pbf', PBFReport, ['clinic'], 'aremind.notifications.idle_facilities.PBFIdleFacilitiesNotificationType')
