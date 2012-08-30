import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from alerts.models import Notification, NotificationVisibility
from mock import patch, Mock
from threadless_router.tests.base import SimpleRouterMixin

from aremind.tests.testcases import CreateDataTest
from aremind.apps.dashboard.tests.base import DashboardDataTest
from aremind.apps.dashboard.models import ReportComment


class AddMessageTest(DashboardDataTest):
    "AJAX view for adding new staff notes or messaging beneficiaries."

    def setUp(self):
        self.url = reverse('fadama_new_message')
        self.user = User.objects.create_user(username='test', password='test', email=u'')
        self.client.login(username='test', password='test')
        self.report = self.create_feedback_report()
        
    def test_post_required(self):
        "View should reject non-post requests."
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_submit_staff_note(self):
        "Submit a new note for the staff."
        data = {
            'report': self.report.pk,
            'comment_type': 'note',
            'author': 'test',
            'text': 'Test Note',
        }
        with patch('aremind.apps.dashboard.utils.fadama.Router') as router:
            # Mock the Router
            MockRouter = Mock()
            router.return_value = MockRouter
            response = self.client.post(self.url, data=data)
            self.assertEqual(response.status_code, 200)
            comment = ReportComment.objects.filter(report=self.report)
            self.assertTrue(comment.exists(), "ReportComment should be created.")

    def test_submit_beneficiary_messsage(self):
        "Submit a message to the report beneficiary."
        data = {
            'report': self.report.pk,
            'comment_type': 'inquiry',
            'author': 'test',
            'text': 'Test Note',
        }
        with patch('aremind.apps.dashboard.utils.fadama.Router') as router:
            # Mock the Router
            MockRouter = Mock()
            router.return_value = MockRouter
            response = self.client.post(self.url, data=data)
            self.assertEqual(response.status_code, 200)
            comment = ReportComment.objects.filter(report=self.report)
            self.assertTrue(comment.exists(), "ReportComment should be created.")

    def test_beneficiary_messsage_sms(self):
        "A beneficiary message should send an SMS to the beneficiary."
        data = {
            'report': self.report.pk,
            'comment_type': 'inquiry',
            'author': 'test',
            'text': 'Test Note',
        }
        with patch('aremind.apps.dashboard.utils.fadama.Router') as router:
            # Mock the Router to capture message passed to outgoing
            MockRouter = Mock()
            router.return_value = MockRouter
            self.client.post(self.url, data=data)
            self.assertTrue(MockRouter.outgoing.called)
            args, kwargs = MockRouter.outgoing.call_args
            msg = args[0]
            # Original text should be present
            self.assertTrue('Test Note' in msg.text)
            # Prefix text
            self.assertTrue(msg.text.lower().startswith('from fadama'))

    def test_staff_messsage_sms(self):
        "A staff message should not send an SMS."
        data = {
            'report': self.report.pk,
            'comment_type': 'note',
            'author': 'test',
            'text': 'Test Note',
        }
        with patch('aremind.apps.dashboard.utils.fadama.Router') as router:
            # Mock the Router to capture message passed to outgoing
            MockRouter = Mock()
            router.return_value = MockRouter
            self.client.post(self.url, data=data)
            self.assertFalse(MockRouter.outgoing.called, "No message should be sent.")


class DismissNotificationTest(CreateDataTest):
    "AJAX view for dismissing a rapidsms-alerts notification."

    def setUp(self):
        self.notification = self.create_notification()
        self.url = reverse('fadama_dismiss_alert', args=[self.notification.id, ])
        self.user = User.objects.create_user(username='test', password='test', email=u'')
        self.client.login(username='test', password='test')
        self.visibility = NotificationVisibility.objects.create(
            notif=self.notification, user=self.user, esc_level=self.notification.escalation_level
        )

    def create_notification(self, **kwargs):
        "Create a notification for testing purposes."
        defaults = {
            'uid': self.random_string(),
            'escalated_on': datetime.datetime.now(),
            'text': self.random_string(),
            'alert_type': 'aremind.notifications.idle_facilities.IdleFacilityNotificationType',
            'escalation_level': 'everyone',
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    def test_dismiss_alert(self):
        "Dismiss alert by sending a DELETE request to the server."
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        visible = self.user.alerts_visible.filter(pk=self.notification.pk).exists()
        self.assertFalse(visible, "Notification should no longer be visible.")

    def test_dismiss_with_post(self):
        "POST will also dismiss the alert."
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        visible = self.user.alerts_visible.filter(pk=self.notification.pk).exists()
        self.assertFalse(visible, "Notification should no longer be visible.")

    def test_get_not_allowed(self):
        "GET requests to this alert are not allowed."
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        visible = self.user.alerts_visible.filter(pk=self.notification.pk).exists()
        self.assertTrue(visible, "Notification should still be visible.")

    def test_notification_not_found(self):
        "Handle the case where notification for the given id does not exist."
        self.notification.delete()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)

    def test_alredy_dismissed(self):
        "Handle the case where notification which has already been dismissed."
        self.visibility.delete()
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)
