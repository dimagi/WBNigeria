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
        self.connection = Connection.objects.create(backend=self.backend, identity='1112223333')
        
    def test_matched_report_id(self):
        "App should handle message which contain report ids."
        report_id = 1234
        text = u'Ok. R{0}'.format(report_id)
        msg = IncomingMessage(self.connection, text)
        handled = self.app.handle(msg)
        self.assertTrue(handled, "Message should be handled.")

    def test_create_report_comment(self):
        "When a report id is matched a corresponding ReportComment should be created."
        report_id = 1234
        text = u'Ok. R{0}'.format(report_id)
        msg = IncomingMessage(self.connection, text)
        self.app.handle(msg)
        comment = ReportComment.objects.get(report_id=report_id, comment_type=ReportComment.REPLY_TYPE)
        self.assertEqual(comment.text, u'Ok. ')

    def test_no_report_id(self):
        "App should not handle messages which don't contain a reply id."
        text = u'Ok.'
        msg = IncomingMessage(self.connection, text)
        handled = self.app.handle(msg)
        self.assertFalse(handled, "Message should not be handled.")
