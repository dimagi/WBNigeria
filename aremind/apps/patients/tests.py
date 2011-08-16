"""
Tests for the appointment patients app.
"""

import datetime
import logging
import random
import re
from lxml import etree

from django.test import TestCase
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission
from django.core.exceptions import ValidationError

from rapidsms.tests.harness import MockRouter, MockBackend
from rapidsms.messages.incoming import IncomingMessage
from rapidsms.messages.outgoing import OutgoingMessage

from aremind.apps.groups.models import Group
from aremind.apps.patients import models as patients
from aremind.apps.patients.forms import PatientRemindersForm
from aremind.tests.testcases import (CreateDataTest, FlushTestScript,
                                    patch_settings)
from aremind.apps.patients.importer import parse_payload, parse_patient
from aremind.apps.wisepill.models import WisepillMessage

from threadless_router.router import Router
from threadless_router.tests.base import SimpleRouterMixin


class PatientsCreateDataTest(CreateDataTest):
    # add patients-specific create_* methods here as needed

    def _node(self, name, value=None):
        element = etree.Element(name)
        if value:
            element.text = value
        return element

    def create_xml_patient(self, data=None):
        """
        <Table>
            <Subject_Number>xxx-nnnnn</Subject_Number>
            <Date_Enrolled>Mar  8 2011 </Date_Enrolled>
            <Mobile_Number>08-11111111</Mobile_Number>
            <Pin_Code>1234</Pin_Code>
            <Next_Visit>Apr  7 2011 </Next_Visit>
            <Reminder_Time>12:00</Reminder_Time>
            <Daily_Doses>0</DailyDoses>
            <Manual_Adherence>19</ManualAdherence>
        </Table>
        """
        data = data or {}
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=random.randint(1, 10) * -1)
        enrolled = now - delta
        delta = datetime.timedelta(days=random.randint(1, 10))
        next_visit = now + delta
        defaults = {
            'Subject_Number': self.random_string(10),
            'Pin_Code': self.random_number_string(4),
            'Date_Enrolled': enrolled.strftime('%b  %d %Y '),
            'Next_Visit': next_visit.strftime('%b  %d %Y '),
            'Mobile_Number': '12223334444',
            'Daily_Doses': '0',
            'Manual_Adherence': '19',
        }
        defaults.update(data)
        empty_items = [k for k, v in defaults.iteritems() if not v]
        for item in empty_items:
            del defaults[item]
        root = self._node('Table')
        for key, value in defaults.iteritems():
            root.append(self._node(key, value))
        return root

    def create_xml_payload(self, nodes):
        root = self._node('NewDataSet')
        for node in nodes:
            root.append(node)
        return etree.tostring(root)

    def create_payload(self, nodes):
        raw_data = self.create_xml_payload(nodes)
        return patients.PatientDataPayload.objects.create(raw_data=raw_data)

    def create_patient(self, data=None):
        data = data or {}
        today = datetime.date.today()
        defaults = {
            'subject_number': self.random_string(12),
            'mobile_number': self.random_number_string(15),
            'pin': self.random_number_string(4),
            'date_enrolled': today,
            'next_visit': today + datetime.timedelta(weeks=1),
            'daily_doses': 2,
            'manual_adherence': 19,
        }
        defaults.update(data)
        if 'contact' not in defaults:
            defaults['contact'] = self.create_contact()
        return patients.Patient.objects.create(**defaults)


class ImportTest(PatientsCreateDataTest):

    def setUp(self):
        self.user = User.objects.create_user('test', 'a@b.com', 'pass')
        self.url = reverse('patient-import')

    def _authorize(self):
        self.client.login(username='test', password='pass')
        permission = Permission.objects.get(codename='add_patientdatapayload')
        self.user.user_permissions.add(permission)

    def _get(self, data={}):
        return self.client.get(self.url, content_type='text/xml')

    def _post(self, data={}):
        return self.client.post(self.url, data, content_type='text/xml')

    def test_view_security(self):
        """ Make sure patient import view has proper security measures """
        # create empty XML payload
        data = self._node('NewDataSet')
        data = etree.tostring(data)
        # GET method not allowed
        response = self._get(data)
        self.assertEqual(response.status_code, 405)
        # Unauthorized, requires add_patientdatapayload permission
        self.client.login(username='test', password='pass')
        response = self._post(data)
        self.assertEqual(response.status_code, 401)
        permission = Permission.objects.get(codename='add_patientdatapayload')
        self.user.user_permissions.add(permission)
        response = self._post(data)
        self.assertEqual(response.status_code, 200)

    def test_payload_patient_creation(self):
        """ Test basic import through the entire stack """
        self._authorize()
        data = {
            'Subject_Number': '000-1111',
            'Pin_Code': '1234',
            'Date_Enrolled': datetime.datetime.now().strftime('%b  %d %Y '),
            'Mobile_Number': '12223334444',
        }
        patient = self.create_xml_patient(data)
        payload = self.create_xml_payload([patient])
        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        created = patients.Patient.objects.all()
        self.assertEqual(created.count(), 1)

    def test_invalid_xml(self):
        """ Invalid XML should raise a validation error """
        data = '---invalid xml data---'
        payload = patients.PatientDataPayload.objects.create(raw_data=data)
        self.assertRaises(ValidationError, parse_payload, payload)
        payload = patients.PatientDataPayload.objects.all()[0]
        self.assertEqual(payload.status, 'error')
        self.assertNotEqual(payload.error_message, '')

    def test_email_sent_on_failure(self):
        """ Failed XML payloads should send email to ADMINS """
        self._authorize()
        data = {
            'Subject_Number': '000-1111',
            'Pin_Code': '1234',
            'Date_Enrolled': datetime.datetime.now().strftime('%b  %d %Y '),
            'Mobile_Number': '2223334444',
        }
        patient = self.create_xml_patient(data)
        payload = self.create_xml_payload([patient])
        response = self._post(payload)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(mail.outbox), 1)

    def test_patient_creation(self):
        """ Test that patients get created properly """
        node = self.create_xml_patient({'Mobile_Number': '12223334444'})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        payload = patients.PatientDataPayload.objects.all()[0]
        self.assertEqual(payload.status, 'success')
        created = patients.Patient.objects.all()
        self.assertEqual(created.count(), 1)
        self.assertEqual(created[0].mobile_number, '12223334444')
        self.assertEqual(created[0].raw_data.pk, payload.pk)
        self.assertTrue(created[0].contact is not None)

    def test_patient_creation_without_country_code(self):
        """ Test patients missing country code are still inserted """
        node = self.create_xml_patient({'Mobile_Number': '2223334444'})
        payload = self.create_payload([node])
        with patch_settings(COUNTRY_CODE='66'):
            parse_patient(node, payload)
            created = patients.Patient.objects.all()
            self.assertEqual(created[0].mobile_number, '662223334444')

    def test_invalid_patient_field(self):
        """ Invalid patient data should return a 500 status code """
        self._authorize()
        patient = self.create_xml_patient({'Mobile_Number': 'invalid'})
        payload = self.create_xml_payload([patient])
        response = self._post(payload)
        self.assertEqual(response.status_code, 500)

    def test_new_contact_association(self):
        """ Test that contacts get created for patients """
        node = self.create_xml_patient({'Mobile_Number': '12223334444',
                                        'Pin_Code': '4444'})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        patient = payload.patients.all()[0]
        self.assertTrue(patient.contact is not None)
        self.assertEqual(patient.contact.phone, '12223334444')
        self.assertEqual(patient.contact.pin, '4444')

    def test_update_contact_association(self):
        """ Test that contacts get updated for patients """
        patient1 = self.create_patient({'mobile_number': '12223334444'})
        patient2 = self.create_patient()
        subject_number = patient1.subject_number
        node = self.create_xml_patient({'Subject_Number': subject_number,
                                        'Mobile_Number': '43332221111'})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        patient = payload.patients.all()[0]
        self.assertNotEqual(patient.pk, patient2.pk)
        self.assertEqual(patient.pk, patient1.pk)
        self.assertNotEqual(patient.contact.pk, patient2.contact.pk)
        self.assertEqual(patient.contact.pk, patient1.contact.pk)
        self.assertEqual(patient.mobile_number, '43332221111')
        self.assertEqual(patient.contact.phone, '43332221111')

    def test_multi_patient_creation(self):
        """ Test that multiple patients are inserted properly """
        node1 = self.create_xml_patient()
        node2 = self.create_xml_patient()
        node3 = self.create_xml_patient()
        payload = self.create_payload([node1, node2, node3])
        parse_payload(payload)
        payload = patients.PatientDataPayload.objects.all()[0]
        self.assertEqual(payload.status, 'success')
        self.assertEqual(payload.patients.count(), 3)

    def test_formatted_number(self):
        """ Test that contacts get created for patients """
        node = self.create_xml_patient({'Mobile_Number': '(33)-0001112222'})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        patient = payload.patients.all()[0]
        self.assertEqual(patient.contact.phone, '330001112222')

    def test_next_visit_not_required(self):
        """ Next_Visit shoudn't be required """
        node = self.create_xml_patient({'Next_Visit': ''})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        self.assertEqual(payload.patients.count(), 1)

    def test_reminder_time(self):
        """ Parse patient preferred reminder time """
        node = self.create_xml_patient({'Reminder_Time': '12:00'})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        self.assertEqual(payload.patients.count(), 1)
        patient = payload.patients.all()[0]
        self.assertEqual(patient.reminder_time, datetime.time(12, 0))

    def test_reminder_time_format(self):
        """ Errors parsing Reminder_Time """
        node = self.create_xml_patient({'Reminder_Time': 'XX:XX'})
        payload = self.create_payload([node])
        self.assertRaises(ValidationError, parse_payload, payload)

    def test_reminder_time_not_required(self):
        """ Reminder_Time is not required """
        node = self.create_xml_patient({'Reminder_Time': ''})
        payload = self.create_payload([node])
        parse_patient(node, payload)
        self.assertEqual(payload.patients.count(), 1)
        patient = payload.patients.all()[0]
        self.assertFalse(patient.reminder_time)


    def test_patient_reminders_form(self):
        contact = self.create_contact()
        data = { 'contact': contact,
                'subject_number': 'foo',
                'mobile_number': '999555121212',
                'daily_doses': 1,
                }
        form = PatientRemindersForm(data)
        if form.is_valid():
            form.save()
        else:
            self.fail("Form did not validate: %r" % form.errors)

class WisepillAdherenceTest(PatientsCreateDataTest):

    def setUp(self):
        self.patient = self.create_patient()
        self.patient.msisdn = self.random_string(12)
        self.patient.daily_doses = 1
        self.patient.manual_adherence = 19
        self.patient.save()

    def create_message_for_patient(self, timestamp):
        msg = WisepillMessage(sms_message='', # ignore
                              timestamp = timestamp,
                              msisdn = self.patient.wisepill_msisdn,
                              patient = self.patient)
        msg.save()

    def days_ago(self, n):
        """Return a datetime object from N days ago"""
        return datetime.datetime.now() - datetime.timedelta(days=n)

    def test_adherence_doseless(self):
        """If patient is not required to take any doses,
        then their adherence is 100% by definition"""
        self.patient.daily_doses = 0
        self.patient.save()
        self.assertEqual(self.patient.adherence(), 100)

    def test_adherence_no_messages(self):
        """If patient is supposed to take doses, but we've
        never seen a message from them (before today),
        adherence is whatever manual says."""
        self.assertEqual(self.patient.adherence(),
                         self.patient.manual_adherence)

    def test_adherence_one_day(self):
        """If we only have one day's data, use manual number"""
        self.create_message_for_patient(self.days_ago(1))
        self.assertEqual(self.patient.adherence(),
                         self.patient.manual_adherence)

    def test_adherence_eight_day(self):
        for n in range(9):
            print "Creating message for %d days ago" % n
            self.create_message_for_patient(self.days_ago(n))
        self.assertEqual(self.patient.adherence(), 100)
    
    def test_adherence_set_min_days(self):
        save_setting = getattr(settings, "MIN_DAYS_TO_COMPUTE_ADHERENCE", None)
        try:
            setattr(settings, "MIN_DAYS_TO_COMPUTE_ADHERENCE", 10)
            for n in range(9):
                print "Creating message for %d days ago" % n
                self.create_message_for_patient(self.days_ago(n))
            self.assertEqual(self.patient.adherence(),
                             self.patient.manual_adherence)
            setattr(settings, "MIN_DAYS_TO_COMPUTE_ADHERENCE", 5)
            self.assertEqual(self.patient.adherence(), 100)
        finally:
            if save_setting:
                setattr(settings, "MIN_DAYS_TO_COMPUTE_ADHERENCE", save_setting)
            else:
                delattr(settings, "MIN_DAYS_TO_COMPUTE_ADHERENCE")

    def test_today_doesnt_count(self):
        self.create_message_for_patient(self.days_ago(0))
        self.assertEqual(self.patient.adherence(),
                         self.patient.manual_adherence)

    def test_max_is_100(self):
        """2 doses per day is not 200% adherence"""
        for n in range(9):
            print "Creating message for %d days ago" % n
            self.create_message_for_patient(self.days_ago(n))
            self.create_message_for_patient(self.days_ago(n))
        self.assertEqual(self.patient.adherence(), 100)

    def test_adherence_cheating(self):
        """For now, cheating works; waiting for answer from Rowena
        on whether to close that hole, but for now, make the behavior
        explicit and test for it.

        (By cheating, I mean opening the box many times on one day
        to 'make up' for missing doses on other days.)"""

        # establish they've had the box a while
        self.create_message_for_patient(self.days_ago(20))
        # do a whole bunch of doses on the same day, yesterday
        for n in range(7):
            self.create_message_for_patient(self.days_ago(1))
        self.assertEqual(self.patient.adherence(), 100)

    def test_rounding(self):
        """Adherence is rounded to nearest integer"""
        self.create_message_for_patient(self.days_ago(7))
        self.create_message_for_patient(self.days_ago(5))
        self.create_message_for_patient(self.days_ago(3))
        self.create_message_for_patient(self.days_ago(1))
        self.assertEqual(self.patient.adherence(), 57)


    def test_validate_manual_adherence(self):
        self.patient.manual_adherence = -1
        self.assertRaises(ValidationError, _validate_patient, self.patient)
        self.patient.manual_adherence = 0
        _validate_patient(self.patient)
        self.patient.manual_adherence = 100
        _validate_patient(self.patient)
        self.patient.manual_adherence = 101
        self.assertRaises(ValidationError, _validate_patient, self.patient)

    def test_one_day_to_reach_level(self):
        """Test calculating the number of days to get back to 95% adherence"""

        # Missed 7 days ago. 
        # If they take tomorrow's dose they will be 100% for the week
        for n in range(7):
            self.create_message_for_patient(self.days_ago(n))
        for n in range(8, 10):
            self.create_message_for_patient(self.days_ago(n))
        self.assertEqual(self.patient.adherence(), 85)
        days = self.patient.days_to_reach_level()
        self.assertEqual(days, 1)

    def test_no_more_than_seven_days(self):
        """Test patient at 0 adherence"""
        self.create_message_for_patient(self.days_ago(10))
        days = self.patient.days_to_reach_level()
        self.assertEqual(days, 7)

    def test_no_doses_to_reach_level(self):
        """Test patient with no doses"""
        self.patient.daily_doses = 0
        self.patient.save()
        days = self.patient.days_to_reach_level()
        self.assertEqual(days, 0)

    def test_already_above_level(self):
        """Test patient already above 95%"""
        for n in range(9):
            self.create_message_for_patient(self.days_ago(n))
        days = self.patient.days_to_reach_level()
        self.assertEqual(days, 0)

    def test_days_to_reach_level_multiple_doses(self):
        """
        Test calculating the number of days to get back to 95% adherence
        when patient takes multiple doses a day
        """

        self.patient.daily_doses = 3
        self.patient.save()

        # Take two pills every third other day and otherwise 3
        for n in range(9):
            if n % 3 != 2:
                self.create_message_for_patient(self.days_ago(n))
            self.create_message_for_patient(self.days_ago(n))
            self.create_message_for_patient(self.days_ago(n))
        self.assertEqual(self.patient.adherence(), 90)
        days = self.patient.days_to_reach_level()
        # It will take 3 days for the first miss day to drop out
        self.assertEqual(days, 3)
        

def _validate_patient(patient):
    patient.full_clean()
                          
