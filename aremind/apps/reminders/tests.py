"""
Tests for the appointment reminders app.
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
from aremind.apps.patients.models import Patient
from aremind.apps.patients.tests import PatientsCreateDataTest
from aremind.apps.reminders import models as reminders
from aremind.tests.testcases import (CreateDataTest, FlushTestScript,
                                    patch_settings)
from aremind.apps.reminders.app import RemindersApp

from threadless_router.router import Router
from threadless_router.tests.base import SimpleRouterMixin


class RemindersCreateDataTest(PatientsCreateDataTest):

    def create_notification(self, data=None):
        data = data or {}
        defaults = {
            'num_days': random.choice(reminders.Notification.NUM_DAY_CHOICES)[0],
            'time_of_day': '12:00',
            'recipients': random.choice(reminders.Notification.RECIPIENTS_CHOICES)[0],
        }
        defaults.update(data)
        return reminders.Notification.objects.create(**defaults)

    def create_sent_notification(self, data=None):
        data = data or {}
        today = datetime.date.today()
        defaults = {
            'status': random.choice(reminders.SentNotification.STATUS_CHOICES)[0],
            'appt_date': today,
            'date_queued': today,
            'date_to_send': today,
            'message': self.random_string(length=100),
        }
        defaults.update(data)
        if 'recipient' not in defaults:
            defaults['recipient'] = self.create_patient().contact
        if 'notification' not in defaults:
            defaults['notification'] = self.create_notification()
        return reminders.SentNotification.objects.create(**defaults)

    def create_confirmed_notification(self, patient, appt_date=None):
        appt_date = appt_date or datetime.date.today()
        return self.create_sent_notification(data={
            'status': 'confirmed',
            'date_sent': appt_date - datetime.timedelta(days=1),
            'date_confirmed': appt_date - datetime.timedelta(days=1),
            'appt_date': appt_date,
            'recipient': patient.contact
        })

    def create_unconfirmed_notification(self, patient, appt_date=None):
        appt_date = appt_date or datetime.date.today()
        return self.create_sent_notification(data={
            'status': 'sent',
            'date_sent': appt_date - datetime.timedelta(days=1),
            'date_confirmed': None,
            'appt_date': appt_date,
            'recipient': patient.contact
        })


class ViewsTest(RemindersCreateDataTest):

    def setUp(self):
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.user.save()
        self.client.login(username='test', password='abc')
        self.dashboard_url = reverse('reminders_dashboard')

    def get_valid_data(self):
        data = {
            'num_days': random.choice(reminders.Notification.NUM_DAY_CHOICES)[0],
            'time_of_day': '12:00',
            'recipients': random.choice(reminders.Notification.RECIPIENTS_CHOICES)[0],
        }
        return data

    def test_notification_schedule(self):
        """
        Test that the notification schedule loads properly.
        """

        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        
    def test_get_create_page(self):
        """
        Test retriving the create notification schedule form.
        """

        url = reverse('create-notification')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_notification(self):
        """
        Test creating notification via form.
        """

        start_count = reminders.Notification.objects.count()
        url = reverse('create-notification')
        data = self.get_valid_data()
        response = self.client.post(url, data)
        self.assertRedirects(response, self.dashboard_url)
        end_count = reminders.Notification.objects.count()
        self.assertEqual(end_count, start_count + 1)

    def test_get_edit_page(self):
        """
        Test retriving the edit notification schedule form.
        """

        data = self.get_valid_data()
        notification = reminders.Notification.objects.create(**data)
        url = reverse('edit-notification', args=[notification.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_edit_notification(self):
        """
        Test editing notification via form.
        """

        data = self.get_valid_data()
        notification = reminders.Notification.objects.create(**data)
        start_count = reminders.Notification.objects.count()
        url = reverse('edit-notification', args=[notification.pk])
        response = self.client.post(url, data)
        self.assertRedirects(response, self.dashboard_url)
        end_count = reminders.Notification.objects.count()
        self.assertEqual(end_count, start_count)

    def test_get_delete_page(self):
        """
        Test retriving the delete notification schedule form.
        """

        data = self.get_valid_data()
        notification = reminders.Notification.objects.create(**data)
        url = reverse('delete-notification', args=[notification.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_notification(self):
        """
        Test delete notification via form.
        """

        data = self.get_valid_data()
        notification = reminders.Notification.objects.create(**data)
        start_count = reminders.Notification.objects.count()
        url = reverse('delete-notification', args=[notification.pk])
        response = self.client.post(url, data)
        self.assertRedirects(response, self.dashboard_url)
        end_count = reminders.Notification.objects.count()
        self.assertEqual(end_count, start_count - 1)


class RemindersConfirmHandlerTest(RemindersCreateDataTest):

    def setUp(self):
        self.contact = self.create_contact()
        self.backend = self.create_backend(data={'name': 'mockbackend'})
        self.unreg_conn = self.create_connection({'backend': self.backend})
        self.reg_conn = self.create_connection({'contact': self.contact,
                                                'backend': self.backend})
        self.router = MockRouter()
        self.app = RemindersApp(router=self.router)

    def _send(self, conn, text):
        msg = IncomingMessage(conn, text)
        self.app.handle(msg)
        return msg

    def test_unregistered(self):
        """ test the response from an unregistered user """
        msg = self._send(self.unreg_conn, '1')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.not_registered)

    def test_registered_no_notifications(self):
        """
        test the response from a registered user without any notifications
        """
        msg = self._send(self.reg_conn, '1')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.no_reminders)

    def test_registered_pin_required(self):
        """
        test the response from a registered user without any notifications
        """
        self.contact.pin = '1234'
        self.contact.save()
        msg = self._send(self.reg_conn, '1')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.pin_required)

    def test_registered_incorrect_pin(self):
        """
        test the response from a registered user without any notifications
        """
        self.contact.pin = '1234'
        self.contact.save()
        msg = self._send(self.reg_conn, '4444')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.incorrect_pin)

    def test_registered_with_notification(self):
        """ test the response from a user with a pending notification """
        now = datetime.datetime.now()
        notification = reminders.Notification.objects.create(num_days=1,
                                                             time_of_day=now)
        reminders.SentNotification.objects.create(notification=notification,
                                                  recipient=self.contact,
                                                  status='sent',
                                                  message='abc',
                                                  appt_date=now,
                                                  date_to_send=now,
                                                  date_queued=now)
        msg = self._send(self.reg_conn, '1')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.thank_you)
        sent_notif = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notif.count(), 1)
        self.assertEqual(sent_notif[0].status, 'confirmed')

    def test_registered_with_notification_and_pin(self):
        """ test the response from a user with a pending notification """
        now = datetime.datetime.now()
        self.contact.pin = '1234'
        self.contact.save()
        notification = reminders.Notification.objects.create(num_days=1,
                                                             time_of_day=now)
        reminders.SentNotification.objects.create(notification=notification,
                                                  recipient=self.contact,
                                                  status='sent',
                                                  message='abc',
                                                  appt_date=now,
                                                  date_to_send=now,
                                                  date_queued=now)
        msg = self._send(self.reg_conn, '1234')
        self.assertEqual(len(msg.responses), 1)
        self.assertEqual(msg.responses[0].text,
                         self.app.thank_you)
        sent_notif = reminders.SentNotification.objects.all()
        self.assertEqual(sent_notif.count(), 1)
        self.assertEqual(sent_notif[0].status, 'confirmed')

    def test_forward_broadcast(self):
        """Confirmations should be forwarded to DEFAULT_CONFIRMATIONS_GROUP_NAME"""
        now = datetime.datetime.now()
        notification = reminders.Notification.objects.create(num_days=1,
                                                             time_of_day=now)
        reminders.SentNotification.objects.create(notification=notification,
                                                  recipient=self.contact,
                                                  status='sent',
                                                  message='abc',
                                                  appt_date=now,
                                                  date_to_send=now,
                                                  date_queued=now)
        msg = self._send(self.reg_conn, '1')
        group = Group.objects.get(name=settings.DEFAULT_CONFIRMATIONS_GROUP_NAME)
        broadcasts = group.broadcasts.filter(schedule_frequency='one-time')
        self.assertEqual(broadcasts.count(), 1)


class RemindersScriptedTest(SimpleRouterMixin, RemindersCreateDataTest):

    def test_scheduler(self):
        contact = self.create_contact({'pin': '1234'})
        backend = self.create_backend(data={'name': 'mockbackend'})
        connection = self.create_connection({'contact': contact,
                                             'backend': backend})
        now = datetime.datetime.now()
        notification = reminders.Notification.objects.create(num_days=1,
                                                             time_of_day=now)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        Patient.objects.create(contact=contact,
                                         date_enrolled=datetime.date.today(),
                                         subject_number='1234',
                                         mobile_number='tester',
                                         next_visit=tomorrow)
        # run cronjob
        from aremind.apps.reminders.app import scheduler_callback
        scheduler_callback(self.router)
        queued = contact.sent_notifications.filter(status='queued').count()
        sent = contact.sent_notifications.filter(status='sent').count()
        # nothing should be queued (future broadcast isn't ready)
        self.assertEqual(queued, 0)
        # only one message should be sent
        self.assertEqual(sent, 1)
        message = contact.sent_notifications.filter(status='sent')[0]
        self.assertTrue(message.date_sent is not None)

    def test_patient_reminder_time(self):
        contact = self.create_contact({'pin': '1234'})
        backend = self.create_backend(data={'name': 'mockbackend'})
        connection = self.create_connection({'contact': contact,
                                             'backend': backend})
        now = datetime.datetime.now()
        notification = reminders.Notification.objects.create(num_days=1,
                                                             time_of_day=now)
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        next_hour = now + + datetime.timedelta(hours=1)
        patient = Patient.objects.create(contact=contact,
                                         date_enrolled=datetime.date.today(),
                                         subject_number='1234',
                                         mobile_number='tester',
                                         next_visit=tomorrow,
                                         reminder_time=next_hour.time())
        # run cronjob
        from aremind.apps.reminders.app import scheduler_callback
        scheduler_callback(self.router)
        queued = contact.sent_notifications.filter(status='queued').count()
        sent = contact.sent_notifications.filter(status='sent').count()
        # patient message should be queued since they have asked for a later time
        self.assertEqual(queued, 1)
        # no messages ready to be sent
        self.assertEqual(sent, 0)
        message = contact.sent_notifications.filter(status='queued')[0]
        self.assertTrue(message.date_sent is None)
        self.assertEqual(message.date_to_send, datetime.datetime.combine(now, patient.reminder_time))


class PatientManagerTest(RemindersCreateDataTest):
    """Tests for patient manager methods"""

    def setUp(self):
        super(PatientManagerTest, self).setUp()
        self.test_patient = self.create_patient()
        self.other_patient = self.create_patient()
        self.unrelated_patient = self.create_patient()

    def test_simple_confirmed(self):
        """Basic confirmed query test."""
        appt_date = datetime.date.today()
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        unconfirmed = self.create_unconfirmed_notification(self.other_patient, appt_date)
        qs = Patient.objects.confirmed_for_date(appt_date)
        self.assertTrue(self.test_patient in qs)
        self.assertFalse(self.other_patient in qs)
        self.assertFalse(self.unrelated_patient in qs)

    def test_simple_unconfirmed(self):
        """Basic unconfirmed query test."""
        appt_date = datetime.date.today()
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        unconfirmed = self.create_unconfirmed_notification(self.other_patient, appt_date)
        qs = Patient.objects.unconfirmed_for_date(appt_date)
        self.assertFalse(self.test_patient in qs)
        self.assertTrue(self.other_patient in qs)
        self.assertFalse(self.unrelated_patient in qs)

    def test_multiple_notifications_confirmed(self):
        """Confirmed patients returned should be distinct."""
        appt_date = datetime.date.today()
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        confirmed_again = self.create_confirmed_notification(self.test_patient, appt_date)
        qs = Patient.objects.confirmed_for_date(appt_date)
        self.assertTrue(self.test_patient in qs)
        self.assertTrue(qs.count(), 1)

    def test_multiple_notifications_unconfirmed(self):
        """Unconfirmed patients returned should be distinct."""
        appt_date = datetime.date.today()
        notified = self.create_unconfirmed_notification(self.test_patient, appt_date)
        notified_again = self.create_unconfirmed_notification(self.test_patient, appt_date)
        qs = Patient.objects.unconfirmed_for_date(appt_date)
        self.assertTrue(self.test_patient in qs)
        self.assertTrue(qs.count(), 1)

    def test_mixed_messages_confirmed(self):
        """Only need to confirm once to be considered confirmed."""
        appt_date = datetime.date.today()
        notified = self.create_unconfirmed_notification(self.test_patient, appt_date)
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        notified_again = self.create_unconfirmed_notification(self.test_patient, appt_date)
        qs = Patient.objects.confirmed_for_date(appt_date)
        self.assertTrue(self.test_patient in qs)
        self.assertTrue(qs.count(), 1)


class DailyReportTest(RemindersCreateDataTest):

    def setUp(self):
        super(DailyReportTest, self).setUp()
        group_name = settings.DEFAULT_DAILY_REPORT_GROUP_NAME
        self.group = self.create_group(data={'name': group_name})
        self.test_contact = self.create_contact(data={'email': 'test@example.com'})
        self.group.contacts.add(self.test_contact)
        self.test_patient = self.create_patient()
        self.other_patient = self.create_patient()
        self.unrelated_patient = self.create_patient()
        self.router = Router()

    def assertPatientInMessage(self, message, patient):
        self.assertTrue(patient.subject_number in message.body)

    def assertPatientNotInMessage(self, message, patient):
        self.assertFalse(patient.subject_number in message.body)

    def test_sending_mail(self):
        """Test email goes out the contacts in the daily report group."""
        # run email job
        from aremind.apps.reminders.app import daily_email_callback
        daily_email_callback(self.router)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertTrue(self.test_contact.email in message.to)

    def test_appointment_date(self):
        """Test email contains info for the appointment date."""
        appt_date = datetime.date.today() + datetime.timedelta(days=7) # Default for email
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        unconfirmed = self.create_unconfirmed_notification(self.other_patient, appt_date)

        # run email job
        from aremind.apps.reminders.app import daily_email_callback
        daily_email_callback(self.router)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertPatientInMessage(message, self.test_patient)
        self.assertPatientInMessage(message, self.other_patient)
        self.assertPatientNotInMessage(message, self.unrelated_patient)

    def test_changing_date(self):
        """Test changing appointment date via callback kwarg."""
        days = 2
        appt_date = datetime.date.today() + datetime.timedelta(days=days)
        confirmed = self.create_confirmed_notification(self.test_patient, appt_date)
        unconfirmed = self.create_unconfirmed_notification(self.other_patient, appt_date)

        # run email job
        from aremind.apps.reminders.app import daily_email_callback
        daily_email_callback(self.router, days=days)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertPatientInMessage(message, self.test_patient)
        self.assertPatientInMessage(message, self.other_patient)
        self.assertPatientNotInMessage(message, self.unrelated_patient)

    def test_skip_blank_emails(self):
        """Test handling contacts with blank email addresses."""
        blank_contact = self.create_contact(data={'email': ''})
        self.group.contacts.add(blank_contact)

        # run email job
        from aremind.apps.reminders.app import daily_email_callback
        daily_email_callback(self.router)

        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(len(message.to), 1)


class ManualConfirmationTest(RemindersCreateDataTest):

    def setUp(self):
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.user.save()
        self.client.login(username='test', password='abc')
        self.test_patient = self.create_patient()
        self.appt_date = datetime.date.today()
        self.unconfirmed = self.create_unconfirmed_notification(self.test_patient, self.appt_date)
        self.url = reverse('manually-confirm-patient', args=[self.unconfirmed.pk])

    def test_get_page(self):
        """Get manual confirmation page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_manually_confirm(self):
        """Test manually confirming a patient reminder."""
        data = {}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('reminders_dashboard'))

        reminder = reminders.SentNotification.objects.get(pk=self.unconfirmed.pk)
        self.assertEqual(reminder.status, 'manual')
        self.assertEqual(reminder.date_confirmed.date(), datetime.date.today())

    def test_redirect(self):
        """Test post redirect."""
        next_url = reverse('reminders-report')
        data = {'next': next_url}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, next_url)

