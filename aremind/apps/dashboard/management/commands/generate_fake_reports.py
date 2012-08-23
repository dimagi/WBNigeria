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
from rapidsms.contrib.locations.models import Location

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
        data.update({
                'site': random_pbf_site(),
                'freeform': random_pbf_message() if random.random() < .3 else None,
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
        complaint_type, complaint_subtype = random_fadama_complaint()

        data.update({
                'site': random_fadama_site(),
                'satisfied': satisfied,
                'freeform': random_fadama_message(satisfied, complaint_type, complaint_subtype),
            })
        r = FadamaReport(**data)
        r.content = {
            complaint_type: complaint_subtype,
        }
        return r





def random_pbf_site():
    return random.choice(Location.objects.filter(type__slug='clinic'))

def random_fadama_site():
    return random.choice(Location.objects.filter(type__slug='fug'))

def random_pbf_message():
    SAMPLE_MESSAGES = [
        'wait too long, doctor no come',
        'no doctor, no drug',
        'good clinic, god bless',
        'clinic is good, doctor is good',
        'People at clinic ask for 5000 naira, i have no money',
        'clinic people help with malaria',
        'feel better now',
        'wait all morning, too many people waiting',
        'clinic is very dirty',
        'bring picken so them no go catch polio',
        'where you see price of treatment?',
        'breast milk only or water for baby',
    ]
    return random.choice(SAMPLE_MESSAGES)

def random_fadama_complaint():
    type = random.choice(utils.fadama.COMPLAINT_TYPES)
    subtype = random.choice(utils.fadama.COMPLAINT_SUBTYPES[type])
    return type, subtype

def random_fadama_message(satisfied, complaint_type, complaint_subtype):
    SAMPLE_MESSAGES = {
        'satisfied': [
            'The project is good because it helps a lot,for example some people don\'t have money 2 feed but with the help of the world bank, people can feed their for them 2',
            'because i have benefited & continue the enterprise',
            'we have been asisted by fadahma with input nd output has inprove',
            'Project is good, god bless',
        ],
        ('people', 'state'): [
            'no answer to my complaint',
            'call the fadama people but no reply',
            'other village say Fadama people visited. no visit here',
        ],
        ('people', 'facilitator'): [
            'facilitator did not come for long time',
            'facilitator not doing anything',
            'you people say facilitator supposed to help. no help',
        ],
        ('people', 'other'): [
            'no answer to my complaint',
            'travel 2 hours but desk officer never at the office',
        ],
        ('people', 'fca'): [
            'people in FCA are leaving their project, chicken project',
            'my brother wants to do Fadama project too',
            'people from my group are cheating',
            'FCA chairman only go to training, I want go to training also',
        ],
        ('people', 'fug'): [
            'people in FCA are leaving their project, chicken project',
            'my brother wants to do Fadama project too',
            'people from my group are cheating',
            'FCA chairman only go to training, I want go to training also',
        ],
        ('financial', 'bank'): [
            'no bank in my village',
            'how to open bank account?',
        ],
        ('financial', 'delay'): [
            'i have no money',
            'Fadama money not coming',
        ],
        ('info', 'input'): [
            'fertilizers are late, yams do not grow',
            'need information for my seedlings',
        ],
        ('info', 'market'): [
            'where to sell my yams?',
            'dont know price for selling my fish',
        ],
        ('info', 'credit'): [
            'need credit',
            'facilitator say there is no credit for my group',
        ],
        ('serviceprovider', 'notfind'): [
            'service provider is too expensive. Help',
            'not finding service provider',
            'no service provider in abuja, only in kaduna state',
        ],
        ('serviceprovider', 'notstarted'): [
            'service provider dont come, construction is late',
            'construction not started',
        ],
        ('serviceprovider', 'delays'): [
            'service provider dont come, construction is late',
            'construction should be completed. now a month late',
        ],
        ('serviceprovider', 'abandon'): [
            'service provider stop working on project',
            'service provider did not come for long time',
        ],
        ('serviceprovider', 'substandard'): [
            'service provider chop my money',
            'construction is bad, door break with the wind',
            'service provider did not deliver on his promise ',
        ],
        ('land', 'notfind'): [
            'group is formed but there is no land',
            'we give the money but Fadama say need land. where to find land?',
        ],
        ('land', 'suitability'): [
            'we found land but people say land not good',
            'why Fadama no accept my land?',
        ],
        ('land', 'ownership'): [
            'someone claims ownership of land',
            'land from council but people want to take it from my group',
        ],
        ('ldp', 'delay'): [
            'waiting on ldp',
            'facilitator writes in ldp that project is fish farming. I want chicken farming',
        ],
    }

    if satisfied:
        messageshuffle = SAMPLE_MESSAGES['satisfied']
        messagelikelihood = .2
    else:
        try:
            messageshuffle = SAMPLE_MESSAGES[(complaint_type, complaint_subtype)]
            messagelikelihood = .8
        except KeyError:
            messagelikelihood = .5
            messageshuffle = SAMPLE_MESSAGES['satisfied']
            for k, v in SAMPLE_MESSAGES.iteritems():
                if k[0] == complaint_type:
                    messageshuffle.extend(SAMPLE_MESSAGES[k])

    return random.choice(messageshuffle) if random.random() < messagelikelihood else None

