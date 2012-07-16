import json
import random
from datetime import datetime, timedelta
from optparse import make_option

from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from django.core.management.base import BaseCommand, CommandError

from aremind.apps.dashboard import views


def true_false():
    return random.random() < .5


class Command(BaseCommand):
    "Command to generate random report data in .json files for dashboard testing."

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
    )

    def handle(self, *args, **options):
        "Main command body."
        mapping = getattr(settings, 'DASHBOARD_SAMPLE_DATA', None)
        if mapping is None:
            raise CommandError(u'You must define DASHBOARD_SAMPLE_DATA in your settings file. '
                u'See the example local settings.')
        count = options.get('count', 1000)
        generate_all = options.get('generate_all', False)
        if generate_all:
            names = mapping.keys()
        else:
            names = args
        for name in names:
            if name not in mapping:
                raise CommandError(u'"{0}" is not defined in the DASHBOARD_SAMPLE_DATA mapping. '
                    u'Valid names: {1}'.format(name, ', '.join(mapping.keys()))
                )
            path = mapping[name]
            func = getattr(self, u'generate_{0}_report'.format(name), self.generate_report)
            reports = map(func, xrange(1, count + 1))
            with open(path, 'w') as f:
                json.dump(reports, f)
            self.stdout.write(u'Saved {0} {1} reports to {1}\n'.format(count, name, path))

    def generate_report(self, index):
        "Generic report generator."
        report = {
            'id': index,
            'timestamp': (datetime.utcnow() - timedelta(days=random.uniform(0, 180))).strftime('%Y-%m-%dT%H:%M:%S'),
            'satisfied': true_false(),
            'message': self.lorem_message() if random.random() < .3 else None
        }
        return report

    def lorem_message(self):
        "Lorem Ipsum message."
        return lorem_ipsum.sentence()

    def generate_pbf_report(self, index):
        "Additional PBF report fields."
        report = self.generate_report(index)
        report['facility'] = random.choice(views.pbf.FACILITIES)['id']
        report['waiting_time'] = random.randint(0, 7)
        report['staff_friendliness'] = true_false()
        report['price_display'] =  true_false()
        report['drug_availability'] =  true_false()
        report['cleanliness'] =  true_false()
        return report

    def generate_fadama_report(self, index):
        "Additional Fadama report fields."
        report = self.generate_report(index)
        facility = random.choice(views.fadama.FACILITIES)
        report['facility'] = facility['id']
        report['fug'] = random.choice(facility['fugs']),
        complaint_type = random.choice(views.fadama.COMPLAINT_TYPES)
        choices = {
            'serviceprovider': [
                'notfind',
                'notstarted',
                'delay',
                'stopped',
                'substandard',
                'other',
            ],
            'people': [
                'state',
                'fug',
                'fca',
                'facilitator',
                'other',
            ],
            'land': [
                'notfind',
                'suitability',
                'ownership',
                'other',
            ],
            'info': [
                'market',
                'input',
                'credit',
                'other',
            ],
            'ldp': [
                'delay',
                'other',
            ],
            'financial': [
                'bank',
                'delay',
                'other',
            ],
        }
        report[complaint_type] = random.choice(choices[complaint_type])
        report['proxy'] = true_false()
        return report
