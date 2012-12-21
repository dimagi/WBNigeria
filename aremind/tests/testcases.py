import datetime
import random
import string
from contextlib import contextmanager

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS
from django.test import TestCase

from rapidsms.models import Connection, Contact, Backend
from rapidsms.contrib.locations.models import Location, LocationType
from threadless_router.tests.scripted import TestScript

from aremind.apps.groups.models import Group
from aremind.apps.dashboard.models import FadamaReport, PBFReport


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

    def create_backend(self, data=None):
        data = data or {}
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Backend.objects.create(**defaults)

    def create_contact(self, data=None):
        data = data or {}
        defaults = {
            'name': self.random_string(12),
        }
        defaults.update(data)
        return Contact.objects.create(**defaults)

    def create_connection(self, data=None):
        data = data or {}
        defaults = {
            'identity': self.random_string(10),
        }
        defaults.update(data)
        if 'backend' not in defaults:
            defaults['backend'] = self.create_backend()
        return Connection.objects.create(**defaults)

    def create_group(self, data=None):
        data = data or {}
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

    def _create_report(self, cls, **kwargs):
        defaults = {
            'timestamp': kwargs.get('timestamp', None) or datetime.datetime.now(),
            'reporter': kwargs.get('reporter', None) or self.create_connection(),
            'site': kwargs.get('site', None) or self.create_location(),
            'proxy': False,
            'can_contact': True,
            'schema_version': 0,
            'freeform': self.random_string(100),
            'raw_report': self.random_string(100),
        }
        defaults.update(kwargs)
        return cls.objects.create(**defaults)

    def create_fadama_report(self, **kwargs):
        self._create_report(FadamaReport, **kwargs)

    def create_pbf_report(self, **kwargs):
        self._create_report(PBFReport, **kwargs)

    def create_user(self, username=None, password=None, email=None):
        username = username or self.random_string(25)
        password = password or self.random_string(25)
        email = email or self.random_string(10) + '@example.com'
        user = User.objects.create_user(username, email, password)
        return user

    def create_location_type(self, **kwargs):
        defaults = {
            'name': self.random_string(25),
            'slug': self.random_string(25),
        }
        defaults.update(**kwargs)
        location_type = LocationType.objects.create(**defaults)
        return location_type

    def create_location(self, **kwargs):
        defaults = {
            'name': self.random_string(25),
            'slug': self.random_string(25),
            'type': kwargs['type'] if 'type' in kwargs else self.create_location_type().id,
        }
        defaults.update(**kwargs)
        location = Location.objects.create(**defaults)
        return location


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
