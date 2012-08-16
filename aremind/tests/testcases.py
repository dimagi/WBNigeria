import datetime
import random
import string
from contextlib import contextmanager

from django.test import TestCase
from django.db import DEFAULT_DB_ALIAS
from django.core.management import call_command

from rapidsms.models import Connection, Contact, Backend
from threadless_router.tests.scripted import TestScript

from aremind.apps.groups.models import Group
from aremind.notifications import REPORT_TIMESTAMP_FORMAT


UNICODE_CHARS = [unichr(x) for x in xrange(1, 0xD7FF)]
MAX_FACILITY_ID = 1000
MAX_REPORT_ID = 1000


class CreateDataTest(TestCase):
    """ Base test case that provides helper functions to create data """

    def random_string(self, length=255, extra_chars=''):
        chars = string.letters + extra_chars
        return ''.join([random.choice(chars) for i in range(length)])

    def random_number_string(self, length=4):
        numbers = [str(x) for x in random.sample(range(10), 4)]
        return ''.join(numbers)

    def random_unicode_string(self, max_length=255):
        output = u''
        for x in xrange(random.randint(1, max_length/2)):
            c = UNICODE_CHARS[random.randint(0, len(UNICODE_CHARS)-1)]
            output += c + u' '
        return output

    def create_backend(self, data={}):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Backend.objects.create(**defaults)

    def create_contact(self, data={}):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Contact.objects.create(**defaults)

    def create_connection(self, data={}):
        defaults = {
            'identity': self.random_string(10),
        }
        defaults.update(data)
        if 'backend' not in defaults:
            defaults['backend'] = self.create_backend()
        return Connection.objects.create(**defaults)

    def create_group(self, data={}):
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Group.objects.create(**defaults)

    def _generate_fug(self):
        return self.random_string(15)

    def random_datetime(self, start, end):
        """Returns a random datetime between start and end."""
        delta = end - start
        seconds_range = abs(delta.days * 24 * 60 * 60 + delta.seconds)
        random_interval = random.randrange(seconds_range)
        return start + datetime.timedelta(seconds=random_interval)

    def create_facility(self, data={}):
        num_fugs = random.randrange(2, 10)
        defaults = {
            'id': int(random.random() * MAX_FACILITY_ID),
            'name': self.random_string(25),
            'lat': random.random() * 180 - 90,
            'long': random.random() * 180 - 90,
            'state': self.random_string(3),
            'fugs': [self._generate_fug() for fug in range(num_fugs)],
        }
        defaults.update(data)
        return defaults

    def create_report(self, data={}, timestamp=None):
        if not timestamp:
            end = datetime.datetime.now()
            start = end.replace(year=end.year - 1)
            timestamp = self.random_datetime(start, end)
        defaults = {
            'id': random.randint(1, MAX_REPORT_ID),
            'message': self.random_string(25),
            'timestamp': timestamp.strftime(REPORT_TIMESTAMP_FORMAT),
            'month': datetime.datetime.strftime(timestamp, '%b %Y'),
            '_month': datetime.datetime.strftime(timestamp, '%Y-%m'),
            'info': self.random_string(25),
            'proxy': random.choice([True, False]),
            'thread': [],
            'satisfied': random.choice([True, False]),
            'facility': random.randint(1, MAX_FACILITY_ID),
            'fug': self._generate_fug(),
        }
        defaults.update(data)
        return defaults


class FlushTestScript(TestScript):
    """ 
    To avoid an issue related to TestCases running after TransactionTestCases,
    extend this class instead of TestScript in RapidSMS. This issue may
    possibly be related to the use of the django-nose test runner in RapidSMS.
    
    See this post and Karen's report here:
    http://groups.google.com/group/django-developers/browse_thread/thread/3fb1c04ac4923e90
    """

    def _fixture_teardown(self):
        call_command('flush', verbosity=0, interactive=False,
                     database=DEFAULT_DB_ALIAS)


class SettingDoesNotExist:
    pass


@contextmanager
def patch_settings(**kwargs):
    from django.conf import settings
    old_settings = []
    for key, new_value in kwargs.items():
        old_value = getattr(settings, key, SettingDoesNotExist)
        old_settings.append((key, old_value))
        setattr(settings, key, new_value)
    yield
    for key, old_value in old_settings:
        if old_value is SettingDoesNotExist:
            delattr(settings, key)
        else:
            setattr(settings, key, old_value)
