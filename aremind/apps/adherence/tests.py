import datetime

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from aremind.apps.adherence.models import Reminder, SendReminder
from aremind.apps.patients.tests import PatientsCreateDataTest


__all__ = (
    'ReminderModelTest',
    'AdherenceDashboardViewTest',
    'CreateReminderViewTest',
    'EditReminderViewTest',
    'DeleteReminderViewTest',
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

