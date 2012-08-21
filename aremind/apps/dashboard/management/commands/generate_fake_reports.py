import json
import random
from datetime import datetime, timedelta
from optparse import make_option

from rapidsms.models import Backend, Connection

from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from django.core.management.base import BaseCommand, CommandError

from aremind.apps.dashboard import utils
from aremind.apps.dashboard.models import *

def true_false(ratio=1.):
    return (random.random() < (ratio / (ratio + 1.)))


class Command(BaseCommand):
    "Command to generate random reports for dashboard testing."

    args = u'<dashboard_name ...>'
    help = u'Generate random test data for dashboard reports.'
    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--count',
            type='int',
            dest='count',
            default=1000,
            help=u'Number of reports to generate.'
        ),
        make_option(
            '-a', '--all',
            action='store_true',
            dest='generate_all',
            default=False,
            help=u'Generate data for all dashboards.'
        ),
        make_option(
            '-w', '--window',
            type='int',
            dest='time_window',
            default=6,
            help=u'Time window to generate over (in months).'
        ),
    )

    def handle(self, *args, **options):
        "Main command body."
        report_types = ['pbf', 'fadama']

        count = options.get('count')
        generate_all = options.get('generate_all')
        time_window = options.get('time_window')
        if generate_all:
            types = report_types
        else:
            types = args

        for t in types:
            if t not in report_types:
                raise CommandError(u'"{0}" is not defined in the DASHBOARD_SAMPLE_DATA mapping. '
                    u'Valid names: {1}'.format(t, ', '.join(report_types))
                )

            generator = getattr(self, u'generate_{0}_report'.format(t))
            for i in xrange(count):
                r = generator(i + 1, time_window)
                r.save()
            self.stdout.write(u'Saved {0} {1} reports\n'.format(count, t))

    def generate_base_report(self, index, time_window):
        "Generic report generator."
        data = {
            'id': index,
            'timestamp': datetime.utcnow() - timedelta(days=random.uniform(0, 30.44 * time_window)),
            'satisfied': true_false(),
            'freeform': lorem_ipsum.sentence() if random.random() < .3 else None,
            'reporter': self.make_conn(),
            'proxy': true_false(0.4),
        }
        return data

    def make_phone_number(self):
        #phone_num_len = 2 # ensures lots of collisions from same phone numbers
        phone_num_len = 9
        return '0' + ''.join(str(random.randint(0, 9)) for i in range(phone_num_len))

    def make_conn(self):
        default_backend = getattr(settings, 'PRIMARY_BACKEND', 'httptester')
        backend, _ = Backend.objects.get_or_create(name=default_backend)
        connection, _ = Connection.objects.get_or_create(backend=backend, identity=self.make_phone_number())
        return connection

    def generate_pbf_report(self, index, *args, **kwargs):
        "Additional PBF report fields."
        data = self.generate_base_report(index, *args, **kwargs)
        from rapidsms.contrib.locations.models import Location
        data.update({
                'site': Location.objects.get(id=1),
#                'facility': random.choice(utils.pbf.FACILITIES)['id'],
                'freeform': random.choice(utils.pbf.SAMPLE_MESSAGES) if random.random() < .3 else None,
            })
        r = PBFReport(**data)
        r.content = {
            'waiting_time': random.randint(0, 7),
            'staff_friendliness': true_false(),
            'price_display': true_false(),
            'drug_availability': true_false(),
            'cleanliness': true_false(),
        }
        return r

    def generate_fadama_report(self, index, *args, **kwargs):
        "Additional Fadama report fields."
        data = self.generate_base_report(index, *args, **kwargs)

        satisfied = true_false(.3)
        facility = random.choice(utils.fadama.FACILITIES)
        complaint_type = random.choice(utils.fadama.COMPLAINT_TYPES)
        complaint_subtype = random.choice(utils.fadama.COMPLAINT_SUBTYPES[complaint_type])

        from rapidsms.contrib.locations.models import Location
        data.update({
                'site': Location.objects.get(id=1),
#                'facility': facility['id'],
#                'fug': random.choice(facility['fugs']),
                'satisfied': satisfied,
                'freeform': utils.fadama.gen_sample_message(satisfied, complaint_type, complaint_subtype),
            })
        r = FadamaReport(**data)
        r.content = {
            complaint_type: complaint_subtype,
        }
        return r
