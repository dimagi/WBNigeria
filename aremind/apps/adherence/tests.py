import datetime

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from aremind.apps.adherence.models import (Reminder, SendReminder, Feed, Entry,
                                           QuerySchedule)
from aremind.apps.patients.tests import PatientsCreateDataTest


__all__ = (
    'ReminderModelTest',
    'AdherenceDashboardViewTest',
    'CreateReminderViewTest',
    'EditReminderViewTest',
    'DeleteReminderViewTest',
    'QueryScheduleTest',
)


class AdherenceCreateDataTest(PatientsCreateDataTest):
    def create_reminder(self, data=None):
        data = data or {}
        noon = datetime.time(12, 00)
        defaults = {
            'time_of_day': noon
        }
        defaults.update(data)            
        return Reminder.objects.create(**defaults)

    def create_feed(self, data=None):
        data = data or {}
        defaults = {
            'name': self.random_string(length=50),
            'active': True
        }
        defaults.update(data)            
        return Feed.objects.create(**defaults)

    def create_entry(self, data=None):
        data = data or {}
        defaults = {
            'content': self.random_string(length=50),
            'published': datetime.datetime.now(),
        }
        defaults.update(data)
        if 'feed' not in defaults:
            defaults['feed'] = self.create_feed()    
        return Entry.objects.create(**defaults)


class ReminderModelTest(AdherenceCreateDataTest):

    def test_get_next_date_daily(self):
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        next_date = reminder.get_next_date()
        self.assertEqual(next_date.date(), today.date())
        self.assertEqual(next_date.time().hour, reminder.time_of_day.hour)
        self.assertEqual(next_date.time().minute, reminder.time_of_day.minute)

    def test_get_next_date_weekly(self):
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour,
            'frequency': Reminder.REPEAT_WEEKLY,
            'weekdays': u'0,2,4' # Mon, Wed, Fri
        })
        next_date = reminder.get_next_date()
        self.assertTrue(next_date.weekday() in [0, 2, 4])
        self.assertEqual(next_date.time().hour, reminder.time_of_day.hour)
        self.assertEqual(next_date.time().minute, reminder.time_of_day.minute)

    def test_basic_reminder_queue(self):
        test_patient = self.create_patient()
        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        reminder.recipients.add(test_patient.contact)
        count = reminder.queue_outgoing_messages()
        self.assertEqual(count, 1)
        self.assertEqual(test_patient.contact.adherence_reminders.count(), 1)

    def test_basic_reminder_messages(self):
        """Send most recent entry from subscribed feeds."""

        test_patient = self.create_patient()
        
        test_feed = self.create_feed()
        test_feed.subscribers.add(test_patient.contact)
        test_entry = self.create_entry(data={
            'feed': test_feed,
            'content': 'Test Message'
        })

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        reminder.recipients.add(test_patient.contact)
        count = reminder.queue_outgoing_messages()
        self.assertEqual(test_patient.contact.adherence_reminders.count(), 1)
        message = test_patient.contact.adherence_reminders.all()[0]
        self.assertEqual(message.message, test_entry.content)

    def test_recent_reminder_messages(self):
        """Send most recent entry from subscribed feeds."""

        test_patient = self.create_patient()
        
        test_feed = self.create_feed()
        test_feed.subscribers.add(test_patient.contact)
        test_entry = self.create_entry(data={
            'feed': test_feed,
            'content': "Test Message"
        })

        other_feed = self.create_feed()
        other_feed.subscribers.add(test_patient.contact)
        other_entry = self.create_entry(data={
            'feed': other_feed,
            'content': "This message is newer"
        })

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        reminder.recipients.add(test_patient.contact)
        count = reminder.queue_outgoing_messages()
        self.assertEqual(test_patient.contact.adherence_reminders.count(), 1)
        message = test_patient.contact.adherence_reminders.all()[0]
        self.assertEqual(message.message, other_entry.content)

    def test_not_subscribed_reminder_messages(self):
        """Entries should be pulled from subscribed feeds."""

        test_patient = self.create_patient()
        
        test_feed = self.create_feed()
        test_feed.subscribers.add(test_patient.contact)
        test_entry = self.create_entry(data={
            'feed': test_feed,
            'content': "Test Message"
        })

        other_feed = self.create_feed()
        other_entry = self.create_entry(data={
            'feed': other_feed,
            'content': "Don't sent this message"
        })

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        reminder.recipients.add(test_patient.contact)
        count = reminder.queue_outgoing_messages()
        self.assertEqual(test_patient.contact.adherence_reminders.count(), 1)
        message = test_patient.contact.adherence_reminders.all()[0]
        self.assertEqual(message.message, test_entry.content)


    def test_inactive_feeds(self):
        """Entries from inactive feeds should not be used."""

        test_patient = self.create_patient()
        
        test_feed = self.create_feed()
        test_feed.subscribers.add(test_patient.contact)
        test_entry = self.create_entry(data={
            'feed': test_feed,
            'content': 'Test Message'
        })

        inactive_feed = self.create_feed(data={'active': False})
        inactive_feed.subscribers.add(test_patient.contact)
        inactive_entry = self.create_entry(data={
            'feed': inactive_feed,
            'content': "Don't sent this message"
        })

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        next_hour = (datetime.datetime.now() + datetime.timedelta(hours=1)).time()
        reminder = self.create_reminder(data={
            'date': yesterday, 'time_of_day': next_hour, 'frequency': Reminder.REPEAT_DAILY
        })
        reminder.recipients.add(test_patient.contact)
        count = reminder.queue_outgoing_messages()
        self.assertEqual(test_patient.contact.adherence_reminders.count(), 1)
        message = test_patient.contact.adherence_reminders.all()[0]
        self.assertEqual(message.message, test_entry.content)


class AdherenceDashboardViewTest(AdherenceCreateDataTest):

    def setUp(self):
        super(AdherenceDashboardViewTest, self).setUp()
        self.url = reverse('adherence-dashboard')
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.client.login(username='test', password='abc')

    def test_get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class CreateReminderViewTest(AdherenceCreateDataTest):
    
    def setUp(self):
        super(CreateReminderViewTest, self).setUp()
        self.url = reverse('adherence-create-reminder')
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.client.login(username='test', password='abc')

    def get_valid_data(self):
        data = {
            'time_of_day': '12:00',
            'recipients': [self.create_patient().contact_id],
            'frequency': Reminder.REPEAT_DAILY,
            'weekdays': [],
        }
        return data

    def test_get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_daily_reminder(self):
        data = self.get_valid_data()
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('adherence-dashboard'))

    def test_create_weekly_reminder(self):
        data = self.get_valid_data()
        data['frequency'] = Reminder.REPEAT_WEEKLY
        data['weekdays'] = [1, 2, 3]
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('adherence-dashboard'))


class EditReminderViewTest(AdherenceCreateDataTest):

    def setUp(self):
        super(EditReminderViewTest, self).setUp()
        self.test_reminder = self.create_reminder()
        self.url = reverse('adherence-edit-reminder', args=[self.test_reminder.pk])
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.client.login(username='test', password='abc')

    def get_valid_data(self):
        data = {
            'time_of_day': '12:00',
            'recipients': [self.create_patient().contact_id],
            'frequency': Reminder.REPEAT_DAILY,
            'weekdays': [],
        }
        return data

    def test_get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_daily_reminder(self):
        data = self.get_valid_data()
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('adherence-dashboard'))

    def test_edit_weekly_reminder(self):
        data = self.get_valid_data()
        data['frequency'] = Reminder.REPEAT_WEEKLY
        data['weekdays'] = [1, 2, 3]
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('adherence-dashboard'))


class DeleteReminderViewTest(AdherenceCreateDataTest):

    def setUp(self):
        super(DeleteReminderViewTest, self).setUp()
        self.test_reminder = self.create_reminder()
        self.url = reverse('adherence-delete-reminder', args=[self.test_reminder.pk])
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.client.login(username='test', password='abc')

    def get_valid_data(self):
        data = {'yes': 'yes'}
        return data

    def test_get_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_delete_reminder(self):
        data = self.get_valid_data()
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('adherence-dashboard'))
        self.assertRaises(Reminder.DoesNotExist, Reminder.objects.get, pk=self.test_reminder.pk)

class QueryScheduleTest(TestCase):

    def setUp(self):
        super(QueryScheduleTest, self).setUp()
        self.user = User.objects.create_user('test', 'a@b.com', 'abc')
        self.assertTrue(self.client.login(username='test', password='abc'),
                        "User login failed")

    def test_start_five_days_ago_never_run(self):
        schedule = QuerySchedule(start_date = datetime.date.today() -
                                       datetime.timedelta(days=5),
                                 time_of_day = datetime.time(hour=0),
                                 last_run = None)
        schedule.save()
        self.assertTrue(schedule.should_run(force=False))
        self.assertTrue(schedule.should_run(force=True))

    def test_start_five_days_ago_run_two_days_ago(self):
        schedule = QuerySchedule(start_date = datetime.date.today() -
                                     datetime.timedelta(days=5),
                                 time_of_day = datetime.time(hour=0),
                                 last_run = datetime.datetime.now() -
                                     datetime.timedelta(days=3))
        schedule.save()
        self.assertFalse(schedule.should_run(force=False))
        self.assertTrue(schedule.should_run(force=True))

    def test_brand_new(self):
        schedule = QuerySchedule(start_date = datetime.date.today(),
                                 time_of_day = datetime.time(hour=0),
                                 last_run = None)
        schedule.save()
        self.assertTrue(schedule.should_run(force=False))
        self.assertTrue(schedule.should_run(force=True))

    def test_not_active(self):
        """Test that inactive schedules don't want to run"""
        schedule = QuerySchedule(start_date = datetime.date.today(),
                                 time_of_day = datetime.time(hour=0),
                                 last_run = None,
                                 active = False)
        schedule.save()
        self.assertFalse(schedule.should_run(force=False))
        self.assertTrue(schedule.should_run(force=True))
        
    def test_delete_view(self):
        """Test using the delete view"""
        # need a schedule, content not important
        schedule = QuerySchedule(start_date = datetime.date.today(),
                                 time_of_day = datetime.time(hour=0),
                                 last_run = None,
                                 active = False)
        schedule.save()
        response = self.client.get(reverse('adherence-delete-query-schedule',
                                           args=(schedule.pk,)),
                                   follow=False)
        self.assertContains(response, 'Are you sure')
        response = self.client.post(reverse('adherence-delete-query-schedule',
                                           args=(schedule.pk,)))
        self.assertRedirects(response, reverse('adherence-dashboard'))
        # our schedule should no longer exist
        self.assertRaises(QuerySchedule.DoesNotExist, QuerySchedule.objects.get,
                          pk=schedule.pk)
