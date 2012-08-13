import json
import random
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Backend, Connection
from threadless_router.router import Router

from aremind.apps.dashboard.models import ReportComment
from aremind.apps.utils.functional import map_reduce


def gen_fugs(prefix, num):
    return ['FUG %s-%d' % (prefix, i + 1) for i in range(num)]


FACILITIES = [
    {'id': 1, 'name': 'Destined FCA', 'lat': 8.958, 'lon': 7.0697, 'state': 'fct', 'fugs': [
            'Oyiza',
            'Onuse',
            'Shuma Dev.',
            'Usako',
            'Habid',
            'Davison',
            'Etko',
            'Sion group',
            'Egba Ebemi',
            'Mutonchi',
            'Wisdom',
            'Alheri Reliable',
            'God\'s grace',
            'Jaaiz women',
            'Yoruba community',
            'Young progressive',
        ]},
#    {'id': 2, 'name': 'Unity FCA', 'lat': 8.9268, 'lon': 7.0858, 'state': 'fct', 'fugs': gen_fugs('Unity', 5)},
    {'id': 3, 'name': 'Anagada 1', 'lat': 9.0333, 'lon': 7.1667, 'state': 'fct', 'fugs': [
            'Godiya Women',
            'Alheri Women',
            'Yabu Farmers',
            'Cassava Women',
            'Anagada Youth',
            'Rehama Women Users Ass.',
            'Yan Samari',
            'Ndakoriko',
            'Na Allah farmers',
            'Gudaba dry season',
            'Amin Tailoring',
            'Namuna kowa Farmers',
            'Allah Nagaba',
        ]},
    {'id': 11, 'name': 'Anagada 2', 'lat': 9.0333, 'lon': 7.1617, 'state': 'fct', 'fugs': [
            'Kutapi',
            'Cassava farmers multipurpose',
            'Wisdom farmers',
            'Okachama',
            'Poultry/livestock agro friendly',
            'Anagada farmers',
            'Gaskiya women',
            'Salam women',
            'Peace',
            'Asejere',
            'Women progress',
            'Akwabwageje women',
            'Hope women',
        ]},
    {'id': 4, 'name': 'Paiko', 'lat': 9.4354, 'lon': 6.6344, 'state': 'fct', 'fugs': [
            'Amano Farmers',
            'Dondonbison Agro Forest',
            'Gbodogun',
            'God Bless',
            'Kautal Hore Fulbe Don Lawal Fulfude',
            'Kautal Hore Sippirde Kosam Mende Fulbe',
            'Mobgal Balal Hore',
            'Paiko Fadama Farmers',
            'Paiko People',
            'Young Farmers',
        ]},
    {'id': 5, 'name': 'Chibiri', 'lat': 8.9014, 'lon': 7.1988, 'state': 'fct', 'fugs': [
            'Abwajnajenu',
            'Afawo Women',
            'All Village Youth',
            'Avinebe',
            'Ayastwa Blacksmirth',
            'Ayebwaka',
            'Ayedo Women',
            'Ayenaje',
            'Chibiri Farmers',
            'Chibiri fishermen',
            'Kuje Disable',
            'Young farmers shetuko',
        ]},
    {'id': 6, 'name': 'Wamba', 'lat': 8.936, 'lon': 8.6057, 'state': 'nasarawa', 'fugs': gen_fugs('Wamba', 6)},
    {'id': 7, 'name': 'Akwanga', 'lat': 8.9063, 'lon': 8.4085, 'state': 'nasarawa', 'fugs': gen_fugs('Akwanga', 13)},
    {'id': 8, 'name': 'Angwa Zaria', 'lat': 9.0133, 'lon': 8.2755, 'state': 'nasarawa', 'fugs': gen_fugs('Angwa', 15)},
    {'id': 9, 'name': 'Arum Tumara', 'lat': 9.0994, 'lon': 8.6504, 'state': 'nasarawa', 'fugs': gen_fugs('Arum', 10)},
    {'id': 10, 'name': 'Yashi Madaki', 'lat': 9.1712, 'lon': 8.673, 'state': 'nasarawa', 'fugs': gen_fugs('Yashi', 8)},
]


def facilities_by_id():
    return map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])


def load_reports(state=None, path=settings.DASHBOARD_SAMPLE_DATA['fadama']):
    with open(path) as f:
        reports = json.load(f)

    facs = facilities_by_id()
    reports = [r for r in reports if state is None or state == facs[r['facility']]['state']]

    comments = ReportComment.objects.all()
    by_report = map_reduce(comments, lambda c: [(c.report_id, c)])

    for r in reports:
        ts = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')
        r['month'] = ts.strftime('%b %Y')
        r['_month'] = ts.strftime('%Y-%m')
        r['thread'] = [c.json() for c in sorted(by_report.get(r['id'], []), key=lambda c: c.date)]

    return reports

COMPLAINT_TYPES = [
    'serviceprovider',
    'people',
    'land',
    'info',
    'ldp',
    'financial',
]

COMPLAINT_SUBTYPES = {
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

def gen_sample_message(satisfied, complaint_type, subtype):
    if satisfied:
        messageshuffle = SAMPLE_MESSAGES['satisfied']
        messagelikelihood = .2
    else:
        try:
            messageshuffle = SAMPLE_MESSAGES[(complaint_type, subtype)]
            messagelikelihood = .8
        except KeyError:
            messagelikelihood = .5
            messageshuffle = SAMPLE_MESSAGES['satisfied']
            for k, v in SAMPLE_MESSAGES.iteritems():
                if k[0] == complaint_type:
                    messageshuffle.extend(SAMPLE_MESSAGES[k])

    return random.choice(messageshuffle) if random.random() < messagelikelihood else None


def main_dashboard_stats(user_state):
    data = load_reports(user_state)

    facilities = facilities_by_id()

    def month_stats(data, label):
        return {
            'total': len(data),
            'satisfaction': map_reduce(data, lambda r: [(r['satisfied'],)], len),
            'by_category': dict((k, len([r for r in data if k in r])) for k in COMPLAINT_TYPES),
            'by_clinic': [[facilities[k], v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    return sorted(map_reduce(data, lambda r: [((r['month'], r['_month']), r)], month_stats).values(), key=lambda e: e['_month'])


def detail_stats(facility_id, user_state):
    data = load_reports(user_state)

    facilities = facilities_by_id()

    filtered_data = [r for r in data if facility_id is None or r['facility'] == facility_id]
    for r in filtered_data:
        r['display_time'] = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%y %H:%M')
        r['site_name'] = facilities[r['facility']]['name']

    def month_detail(data, label):
        categories = ['satisfied']
        categories.extend(COMPLAINT_TYPES)
        return {
            'total': len(data),
            'logs': sorted(data, key=lambda r: r['timestamp'], reverse=True),
            'stats': dict((k, map_reduce(data, lambda r: [(r[k],)] if r.get(k) is not None else [], len)) for k in categories),
            'clinic_totals': [[facilities[k], v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    return sorted(map_reduce(filtered_data, lambda r: [((r['month'], r['_month']), r)], month_detail).values(), key=lambda e: e['_month'])


def _get_connection_from_report(report_id):
    "Return connection for user which submitted a given report."
    # FIXME: Currently uses a dummy connection. Needs to get correct connection
    # when report data is hooked up to the backend.
    default_backend = getattr(settings, 'PRIMARY_BACKEND', 'httptester')
    backend, _ = Backend.objects.get_or_create(name=default_backend)
    connection, _ = Connection.objects.get_or_create(backend=backend, identity='15551234567')
    return connection


def get_inquiry_numbers():
    "Return all phone numbers tied to a submitted report."
    # TODO: It might be desirable to filter to comments in a time range.
    report_ids = ReportComment.objects.filter(
        comment_type=ReportComment.INQUIRY_TYPE
    ).values_list('report_id', flat=True)
    numbers = []
    for report_id in report_ids:
        connection = _get_connection_from_report(report_id)
        numbers.append(connection.identity)
    return numbers


def communicator_prefix():
    return _('From fadama:')


def message_report_beneficiary(report_id, message_text):
    "Send a message to a user based on a report."
    connection = _get_connection_from_report(report_id)
    template = u'{0} {1}'.format(communicator_prefix(), message_text)
    message = OutgoingMessage(connection=connection, template=template)
    router = Router()
    router.outgoing(message)
