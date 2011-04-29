import datetime

from aremind.apps.adherence.models import Reminder, SendReminder
from aremind.apps.patients.tests import PatientsCreateDataTest


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
