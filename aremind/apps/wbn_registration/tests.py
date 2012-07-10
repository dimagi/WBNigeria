"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""


from django.test import TestCase
#from rapidsms.tests.harness import MockRouter, MockBackend
#from rapidsms.messages.incoming import IncomingMessage
#from rapidsms.messages.outgoing import OutgoingMessage
import unittest
from rapidsms.messages.incoming import IncomingMessage
#from rapidsms.tests.scripted import TestScript
from aremind.apps.wbn_registration.app import WBN_RegistrationApp as WBApp
from aremind.apps.reminders.tests import RemindersCreateDataTest, MockRouter


#class MySimpleTestScript(TestScript):
#    apps = (WBApp,)
#    def testRunScript (self):
#        testRegister = """
#        1111 > 1234
#        1111 < Thanks for registering! Is your location Abuja City? Send 1 for YES and 2 for NO
#        1111 > 1
#        1111 < Great! Thanks for registering! We will be in touch shortly
#        """
#        self.runScript(testRegister)
#
#    def testRegister(self):
#            self.assertInteraction("""
#                8005551212 > register as someuser
#                8005551212 < Thank you for registering, as someuser!
#            """)

class RemindersConfirmHandlerTest(RemindersCreateDataTest):

    def setUp(self):
        self.contact = self.create_contact()
        self.backend = self.create_backend(data={'name': 'mockbackend'})
        self.unreg_conn = self.create_connection({'backend': self.backend})
        self.reg_conn = self.create_connection({'contact': self.contact,
                                                'backend': self.backend})
        self.router = MockRouter()
        self.app = WBApp(router=self.router)

    def _send(self, conn, text):
        msg = IncomingMessage(conn, text)
        self.app.handle(msg)
        return msg

    def test_good_registration(self):
        """ test the response from an unregistered user """
        msg = self._send(self.unreg_conn, '1234')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.STRING_REG_REQUEST_CONFIRM)



#
#if __name__ == "__main__":
#    unittest.main()
