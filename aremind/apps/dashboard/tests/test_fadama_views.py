from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from mock import patch, Mock
from threadless_router.tests.base import SimpleRouterMixin

from aremind.tests.testcases import CreateDataTest
from aremind.apps.dashboard.models import ReportComment


class AddMessageTest(CreateDataTest):
    "AJAX view for adding new staff notes or messaging beneficiaries."

    def setUp(self):
        self.url = reverse('fadama_new_message')
        self.user = User.objects.create_user(username='test', password='test', email=u'')
        self.client.login(username='test', password='test')
        
    def test_post_required(self):
        "View should reject non-post requests."
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_submit_staff_note(self):
        "Submit a new note for the staff."
        data = {
            'report_id': 1234,
            'comment_type': 'note',
            'author': 'test',
            'text': 'Test Note',
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        comment = ReportComment.objects.filter(report_id=1234)
        self.assertTrue(comment.exists(), "ReportComment should be created.")

    def test_submit_beneficiary_messsage(self):
        "Submit a message to the report beneficiary."
        data = {
            'report_id': 1234,
            'comment_type': 'inquiry',
            'author': 'test',
            'text': 'Test Note',
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        comment = ReportComment.objects.filter(report_id=1234)
        self.assertTrue(comment.exists(), "ReportComment should be created.")

    def test_beneficiary_messsage_sms(self):
        "A beneficiary message should send an SMS to the beneficiary."
        data = {
            'report_id': 1234,
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
            'report_id': 1234,
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
