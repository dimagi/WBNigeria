import datetime
import mock

from django.contrib.auth.models import User

from alerts.models import Notification, NotificationVisibility
from alerts.utils import trigger

from aremind.apps.dashboard.models import FadamaReport, PBFReport
from aremind.notifications.idle_facilities import IdleFacilitiesNotification, IdleFacilitiesNotificationType
from aremind.tests.testcases import CreateDataTest


class FakeIdleFacilitiesNotificationType(IdleFacilitiesNotificationType):

    def users_for_escalation_level(self, esc_level):
        return User.objects.all()


class IdleFacilitiesNotificationsTestBase(object):
    """Test cases for generation of idle facility Notifications."""

    def setUp(self):
        super(IdleFacilitiesNotificationsTestBase, self).setUp()

        self.loc_type = self.create_location_type()
        self.facility = self.create_location(type=self.loc_type)
        self.period_before_notification = datetime.timedelta(days=7)
        self.slug = self.random_string(10)
        self.locationtype_slugs = [self.loc_type.slug]
        self.alert_type = 'aremind.tests.test_notifications.FakeIdleFacilitiesNotificationType'

        now = datetime.datetime.now()
        then = now - self.period_before_notification
        self.recently = self.random_datetime(then, now)
        self.past = self.random_datetime(then.replace(year=then.year - 1), then)

        self.username = self.random_string(25)
        self.password = self.random_string(25)
        self.user = self.create_user(username=self.username, password=self.password)

    def _generate_notifications(self):
        """Generate notifications using mocked data."""
        generator = IdleFacilitiesNotification(self.slug, self.report_type,
                self.locationtype_slugs, self.alert_type, self.period_before_notification)
        return list(generator())

    def test_notification_no_reports(self):
        """Notification is generated when a facility has no reports."""
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_notification_past_report(self):
        """Notification is generated when a facility has no recent reports."""
        report = self.make_report(site=self.facility, timestamp=self.past)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_no_notification(self):
        """No Notification is generated when a facility has a recent report."""
        report = self.make_report(site=self.facility, timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 0)

    def test_notification_delete(self):
        """Open Notifications are deleted when a new report is received."""
        for notif in self._generate_notifications():
            trigger(notif)  # saves to database.
        report = self.make_report(site=self.facility, timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 0)
        self.assertEquals(Notification.objects.count(), 0)

    def test_update_notification(self):
        """Notification is updated with up-to-date information."""
        for notif in self._generate_notifications():
            trigger(notif)  # saves to database.
        notif_pre = Notification.objects.get()
        report = self.make_report(site=self.facility, timestamp=self.past)
        for notif in self._generate_notifications():
            trigger(notif)
        notif_post = Notification.objects.get()
        self.assertEquals(notif_pre.id, notif_post.id)
        self.assertNotEquals(notif_pre.text, notif_post.text)

    def test_notification_persists(self):
        """Notification persists when no new report is received."""
        notifs = self._generate_notifications()
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_notification_persists_with_irrelevant_report(self):
        """Notification doesn't resolve if unrelated new report is received."""
        notifs = self._generate_notifications()
        irrelevant_facility = self.create_location(type=self.loc_type)
        irrelevant_report = self.make_report(site=irrelevant_facility, timestamp=self.recently)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 1)

    def test_multiple_notifications(self):
        """Notifications are created for each idle facility."""
        facility2 = self.create_location(type=self.loc_type)
        notifs = self._generate_notifications()
        self.assertEquals(len(notifs), 2)

    def test_alert_visibility(self):
        """New notifications should be visible to all users."""
        user2 = self.create_user()
        for notif in self._generate_notifications():
            trigger(notif)  # saves to database & creates Visibility objects.
        notif = Notification.objects.get()

        self.assertEquals(NotificationVisibility.objects.filter(
                user=self.user, notif=notif).count(), 1)
        self.assertEquals(NotificationVisibility.objects.filter(
                user=user2, notif=notif).count(), 1)
        self.assertEquals(NotificationVisibility.objects.count(), 2)


class FadamaIdleFacilitiesTest(IdleFacilitiesNotificationsTestBase, CreateDataTest):
    report_type = FadamaReport

    def make_report(self, **kwargs):
        return self.create_fadama_report(**kwargs)


class PBFIdleFacilitiesTest(IdleFacilitiesNotificationsTestBase, CreateDataTest):
    report_type = PBFReport

    def make_report(self, **kwargs):
        return self.create_pbf_report(**kwargs)
