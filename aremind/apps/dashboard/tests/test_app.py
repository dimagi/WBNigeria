from django.test import TestCase

from rapidsms.messages.incoming import IncomingMessage
from rapidsms.models import Connection, Backend
from threadless_router.tests.base import SimpleRouterMixin

from aremind.apps.dashboard.app import CommunicatorApp
from aremind.apps.dashboard.models import ReportComment


class CommunicatorAppTest(SimpleRouterMixin, TestCase):
    "Handling incoming incoming messages related to beneficiary responses."

    def setUp(self):
        super(CommunicatorAppTest, self).setUp()
        self.app = CommunicatorApp(router=self.router)
        self.router.add_app(self.app)
        self.backend = Backend.objects.create(name=u'MockBackend')
        self.connection = Connection.objects.create(backend=self.backend, identity='15551234567')
        self.comment = ReportComment.objects.create(
            report_id=1, comment_type=ReportComment.INQUIRY_TYPE, author='staff', text='How are you?'
        )
        
    def test_matched_report(self):
        "App should handle message which were related to a report connection."
        text = u'Ok.'
        msg = IncomingMessage(self.connection, text)
        handled = self.app.handle(msg)
        self.assertTrue(handled, "Message should be handled.")

    def test_create_report_comment(self):
        "When a report id is matched a corresponding ReportComment should be created."
        text = u'Ok.'
        msg = IncomingMessage(self.connection, text)
        self.app.handle(msg)
        comment = ReportComment.objects.get(comment_type=ReportComment.REPLY_TYPE)
        self.assertEqual(comment.text, u'Ok.')

    def test_no_report_match(self):
        "App should not handle messages which were related to a report connection"
        connection = Connection.objects.create(backend=self.backend, identity='1112223333')
        text = u'Ok.'
        msg = IncomingMessage(connection, text)
        handled = self.app.handle(msg)
        self.assertFalse(handled, "Message should not be handled.")
