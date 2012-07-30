from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from apps.dashboard.models import *
from django.views.decorators.csrf import csrf_exempt

@login_required
def dashboard(request):
    return render(request, 'dashboard/fadama/dashboard.html')


@login_required
def reports(request):
    return render(request, 'dashboard/fadama/reports.html', {
            'default_site': request.GET.get('site'),
            'default_metric': request.GET.get('metric'),
        })


import json
import random
from datetime import datetime, timedelta
import collections

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

complaint_type = [
    'serviceprovider',
    'people',
    'land',
    'info',
    'ldp',
    'financial',
]

def make_reports(path, n, window=6):
    def mk_report(i):
        messages = {
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

        def tf(ratio=1.):
            return (random.random() < (ratio / (ratio + 1.)))

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

        satisfied = tf(.3)
        type = random.choice(complaint_type)
        try:
            value = random.choice(choices[type])
        except KeyError:
            value = tf()

        if satisfied:
            messageshuffle = messages['satisfied']
            messagelikelihood = .2
        else:
            try:
                messageshuffle = messages[(type, value)]
                messagelikelihood = .8
            except KeyError:
                messagelikelihood = .5
                messageshuffle = messages['satisfied']
                for k, v in messages.iteritems():
                    if k[0] == type:
                        messageshuffle.extend(messages[k])

        facility = random.choice(FACILITIES)
        return {
            'id': i,
            'facility': facility['id'],
            'fug': random.choice(facility['fugs']),
            'timestamp': (datetime.utcnow() - timedelta(days=random.uniform(0, 30.44*window))).strftime('%Y-%m-%dT%H:%M:%S'),
            'satisfied': satisfied,
            type: value,
            'message': random.choice(messageshuffle) if random.random() < messagelikelihood else None,
            'proxy': tf(.4),
        }

    reports = [mk_report(i + 1) for i in range(n)]
    with open(path, 'w') as f:
        json.dump(reports, f)

def api_main(request):
    payload = {
        'stats': main_dashboard_stats(),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def user_state():
    # return state for logged-in user
    return None #'fct'

def main_dashboard_stats():
    data = load_reports(user_state())

    facilities = facilities_by_id()

    def month_stats(data, label):
        return {
            'total': len(data),
            'satisfaction': map_reduce(data, lambda r: [(r['satisfied'],)], len),
            'by_category': dict((k, len([r for r in data if k in r])) for k in complaint_type),
            'by_clinic': [[facilities[k], v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    return sorted(map_reduce(data, lambda r: [((r['month'], r['_month']), r)], month_stats).values(), key=lambda e: e['_month'])

def api_detail(request):
    _site = request.GET.get('site')
    site = int(_site) if _site else None

    payload = {
        'facilities': [f for f in FACILITIES if user_state() is None or f['state'] == user_state()],
        'monthly': detail_stats(site),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def detail_stats(facility_id):
    data = load_reports(user_state())

    facilities = facilities_by_id()

    filtered_data = [r for r in data if facility_id is None or r['facility'] == facility_id]
    for r in filtered_data:
        r['display_time'] = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%y %H:%M')
        r['site_name'] = facilities[r['facility']]['name']

    def month_detail(data, label):
        categories = ['satisfied']
        categories.extend(complaint_type)
        return {
            'total': len(data),
            'logs': sorted(data, key=lambda r: r['timestamp'], reverse=True),
            'stats': dict((k, map_reduce(data, lambda r: [(r[k],)] if r.get(k) is not None else [], len)) for k in categories),
            'clinic_totals': [[facilities[k], v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    return sorted(map_reduce(filtered_data, lambda r: [((r['month'], r['_month']), r)], month_detail).values(), key=lambda e: e['_month'])

def map_reduce(data, emitfunc=lambda rec: [(rec,)], reducefunc=lambda v, k: v):
    """perform a "map-reduce" on the data

    emitfunc(datum): return an iterable of key-value pairings as (key, value). alternatively, may
        simply emit (key,) (useful for reducefunc=len)
    reducefunc(values): applied to each list of values with the same key; defaults to just
        returning the list
    data: iterable of data to operate on
    """
    mapped = collections.defaultdict(list)
    for rec in data:
        for emission in emitfunc(rec):
            try:
                k, v = emission
            except ValueError:
                k, v = emission[0], None
            mapped[k].append(v)

    def _reduce(k, v):
        try:
            return reducefunc(v, k)
        except TypeError:
            return reducefunc(v)

    return dict((k, _reduce(k, v)) for k, v in mapped.iteritems())



@csrf_exempt
def new_message(request):
    rc = ReportComment()
    rc.report_id = int(request.POST.get('id'))
    rc.comment_type = request.POST.get('type')
    rc.author = request.POST.get('user')
    rc.text = request.POST.get('text')
    rc.save()
    return HttpResponse(json.dumps(rc.json()), 'text/json')

def msg_from_bene(request):
    rc = ReportComment()
    rc.report_id = int(request.GET.get('id'))
    rc.comment_type = 'response'
    rc.author = '_bene'
    rc.text = request.GET.get('text')
    rc.save()
    return HttpResponse('ok', 'text/plain')

