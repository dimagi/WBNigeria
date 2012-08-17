import datetime
import mock

from django.contrib.auth.models import User
from django.core import management

from alerts.models import Notification, NotificationVisibility

from aremind import notifications
from aremind.tests.testcases import CreateDataTest


class RapidSMSAlertsTestCase(CreateDataTest):
    """Test cases for generations of application-specific Notifications."""

    def setUp(self):
        super(RapidSMSAlertsTestCase, self).setUp()

        # Mock data used for notification generation.
        self.period_before_notification = datetime.timedelta(days=7)
        self.facilities = {}
        self.reports = []

        now = datetime.datetime.now()
        then = now - self.period_before_notification
        self.recently = self.random_datetime(then, now)
        self.past = self.random_datetime(then.replace(year=then.year - 1), then)

        self.username = self.random_string(25)
        self.password = self.random_string(25)
        self.user = self.create_user(username=self.username, password=self.password)

    def _add_facility(self, data={}):
        """Wraps around create_facility to add facility to self.facilities."""
        f = self.create_facility(data)
        self.facilities[f['id']] = f
        return f

    def _add_report(self, data={}, timestamp=None):
        """Wraps around create_report to add report to self.reports."""
        r = self.create_report(data, timestamp)
        self.reports.append(r)
        return r

    def _generate_notifications(self):
        """Generate notifications using mocked data."""
        with mock.patch.object(notifications, 'facilities_by_id') as facilities_by_id:
            facilities_by_id.return_value = self.facilities
            with mock.patch.object(notifications, 'load_reports') as load_reports:
                load_reports.return_value = self.reports
                notifications.PERIOD_BEFORE_NOTIFICATION = self.period_before_notification
                notifs = list(notifications.trigger_idle_facility_notifications())
        return notifs

    def _trigger_alerts(self):
        """Use management command to trigger notifications with mocked data."""
        with mock.patch.object(notifications, 'facilities_by_id') as facilities_by_id:
            facilities_by_id.return_value = self.facilities
            with mock.patch.object(notifications, 'load_reports') as load_reports:
                load_reports.return_value = self.reports
                notifications.PERIOD_BEFORE_NOTIFICATION = self.period_before_notification
                management.call_command('trigger_alerts')

    def test_notification_no_reports(self):
        """A notification is created when a facility has no reports."""
        facility = self._add_facility()
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_notification_past_report(self):
        """A notification is created when a facility has no recent reports."""
        facility = self._add_facility()
        report = self._add_report(data={'facility': facility['id']}, timestamp=self.past)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_no_notification(self):
        """No notification is created when a facility has recent reports."""
        facility = self._add_facility()
        report = self._add_report(data={'facility': facility['id']}, timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 0)
    
    def test_notification_autoresolve(self):
        """Open Notifications are resolved when a new report is received."""
        facility = self._add_facility()
        notifs = self._generate_notifications()
        report = self._add_report(data={'facility': facility['id']}, timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 0)

    def test_notification_persists(self):
        """Notification does not resolve if no new report is received."""
        facility = self._add_facility()
        notifs = self._generate_notifications()
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_notification_persists_with_irrelevant_report(self):
        """Notification doesn't resolve if unrelated new report is received."""
        facility = self._add_facility()
        notifs = self._generate_notifications()
        irrelevant_facility = self._add_facility()
        irrelevant_report = self._add_report(data={'facility': irrelevant_facility['id']},
                timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_multiple_notifications(self):
        """Notifications are created for each idle facility."""
        facility1 = self._add_facility()
        facility2 = self._add_facility()
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 2)

    def test_alert_visibility(self):
        """New notifications should be visible to all users."""
        user2 = self.create_user()
        facility = self._add_facility()
        self._trigger_alerts()
        notif = Notification.objects.get()
        
        self.assertEquals(NotificationVisibility.objects.filter(
                user=self.user, notif=notif).count(), 1)
        self.assertEquals(NotificationVisibility.objects.filter(
                user=user2, notif=notif).count(), 1)
        self.assertEquals(NotificationVisibility.objects.count(), 2)
