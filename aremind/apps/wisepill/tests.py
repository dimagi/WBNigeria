import datetime
from django.test import TestCase

from rapidsms.models import Contact
from aremind.apps.wisepill.models import WisepillMessage
from aremind.apps.patients.models import Patient, PatientDataPayload
from aremind.apps.patients.importer import parse_payload

class WisepillTest(TestCase):

    patients = [
        { 'subject_number': 'xxx-nnnnn', },
        { 'subject_number': 'yyy-nnnnn', },
        ]

    testmsgs = [
        #                                                   DDMMYYHHMMSS
        { 'raw': '@=03,CN=256771413470,SN=357077005471753,T=190509060959,S=20,B=3800,PC=1,U= balance is UGX 15893. Yo,M=1,CE=0',
          'msisdn': '256771413470',
          'timestamp': datetime.datetime(2009,5,19, 6,9,59),  # yy,mm,dd, hh,mm,ss
          'message_type': WisepillMessage.DELAYED_EVENT,
          'subject_number': 'xxx-nnnnn',  # for fake patient
          },
        { 'raw': '@=03,CN=256123453470,SN=357077005471753,T=010199060959,S=20,B=3800,PC=1,U= balance is UGX 15893. Yo,M=1,CE=0',
          'msisdn': '256123453470',
          'timestamp': datetime.datetime(2099,1,1, 6,9,59),  # yy,mm,dd, hh,mm,ss
          'message_type': WisepillMessage.DELAYED_EVENT,
          'subject_number': 'yyy-nnnnn',  # for fake patient
          },
        { 'raw': 'AT=03,CN=256123453470,SN=357077005471753,T=010199060959,S=20,B=3800,PC=1,U= balance is UGX 15893. Yo,M=1,CE=0',
          'msisdn': '256123453470',
          'timestamp': datetime.datetime(2099,1,1, 6,9,59),  # yy,mm,dd, hh,mm,ss
          'message_type': WisepillMessage.DELAYED_EVENT,
          'subject_number': 'yyy-nnnnn',  # for fake patient
          },
        ]

    def setUp(self):
        # Create some patients to correspond to the test messages
        for p in self.patients:
            contact = Contact(name=p['subject_number'])
            contact.save()
            patient = Patient(subject_number=p['subject_number'],
                              contact=contact)
            patient.save()
        for testmsg in self.testmsgs:
            patient = Patient.objects.get(subject_number=testmsg['subject_number'])
            self.assertTrue(patient is not None)
            patient.wisepill_msisdn = testmsg['msisdn']
            patient.save()
            testmsg['patient'] = patient
            self.assertEquals(patient.wisepill_msisdn,testmsg['msisdn'])

    def test_message_parsing(self):
        for testmsg in self.testmsgs:
            obj = WisepillMessage(sms_message = testmsg['raw'])
            now = datetime.datetime.now()
            obj.save()  # causes the parse
            # make sure we got the data out of the message correctly
            self.assertEquals(testmsg['msisdn'], obj.msisdn)
            self.assertEquals(testmsg['timestamp'], obj.timestamp)
            self.assertEquals(testmsg['message_type'], obj.message_type)
            self.assertEquals(testmsg['raw'], obj.sms_message)
            # make sure the time received is sane
            fudge = abs((now - obj.time_received))
            self.assertTrue(fudge < datetime.timedelta(seconds=10))
            # make sure we found a matching patient
            self.assertEquals(testmsg['patient'], obj.patient)
            self.assertEquals(testmsg['msisdn'], obj.patient.wisepill_msisdn)

    def test_only_parsed_on_creation(self):
        """Test that the raw message is only parsed into the other
        fields when we create the object, so we can edit the object
        later and not have our changes reverted every time we
        save it."""
        obj = WisepillMessage(sms_message = self.testmsgs[0]['raw'])
        obj.save()

        # now change the the sms message and save again
        # other values should not change
        obj.sms_message = self.testmsgs[1]['raw']
        obj.save()
        self.assertEquals(obj.msisdn, self.testmsgs[0]['msisdn'])

    def test_wisepill_message_recognition(self):
        from apps.wisepill.app import WisepillApp
        app = WisepillApp(None)
        class fakemsg(object):
            def __init__(self,text):
                self.text = text
        for testmsg in self.testmsgs:
            msg = fakemsg(testmsg['raw'])
            rc = app.handle(msg)
            self.assertTrue(rc)
            obj = WisepillMessage.objects.get(sms_message = testmsg['raw'])
            obj.delete()
        