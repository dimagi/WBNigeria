from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings

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
    {'id': 2, 'name': 'Unity FCA', 'lat': 8.9268, 'lon': 7.0858, 'state': 'fct', 'fugs': gen_fugs('Unity', 5)},
    {'id': 3, 'name': 'Anagada 1', 'lat': 9.0333, 'lon': 7.1667, 'state': 'fct', 'fugs': [
            'Okadiama',
            'Godiya Women',
            'Alheri Women',
            'Yabu Farmers',
            'Cassava Women',
            'Anagada Youth',
            'Poultry & Livestock Agro Friendly',
            'Kutapi',
            'Rehama Women Users Ass.',
            'Yan Samari',
            'Ndakoriko',
            'Peace',
            'Na Allah farmers',
            'Widows',
            'Amin Tailoring',
            'Namuna kowa Farmers',
            'Allah Nagaba',
        ]},
    {'id': 11, 'name': 'Anagada 2', 'lat': 9.0333, 'lon': 7.1617, 'state': 'fct', 'fugs': gen_fugs('Ana2', 5)},
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


def load_reports(path=settings.DASHBOARD_SAMPLE_DATA['fadama']):
    with open(path) as f:
        reports = json.load(f)

    for r in reports:
        ts = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')
        r['month'] = ts.strftime('%b %Y')
        r['_month'] = ts.strftime('%Y-%m')

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
        messages = [
            'The project is good because it helps a lot,for example some people don\'t have money 2 feed but with the help of the world bank, people can feed their for them 2',
            'because i have benefited & continue the enterprise',
            'we have been asisted by fadahma with input nd output has inprove',
            'Kiwon kaji da kiwon kifi',
            'facilitator did not come for long time',
            'service provider is too expensive. help',
            'people in FCA are leaving their project, chicken project',
            'i have no money',
            'no bank in my village',
            'Project is good, god bless',
            'my brother wants to do Fadama project too',
            'no answer to my complaint',
            'fertilizers are late, yams do not grow',
            'people from my group are cheating',
            'FCA chairman only go to training, I want go to training also',
            'Fadama money not coming',
            'group is formed but there is no land',
            'waiting on ldp',
            'facilitator writes in ldp that project is fish farming. I want chicken farming',
            'travel 2 hours but desk officer never at the office',
            'call the fadama people but no reply',
            'service provider chop my money',
            'service provider dont come, construction is late',
            'where to sell my yams?',
            'dont know price for selling my fish',
            'need information for my seed',
        ]

        def tf():
            return (random.random() < .5)

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

        type = random.choice(complaint_type)
        try:
            value = random.choice(choices[type])
        except KeyError:
            value = tf()

        facility = random.choice(FACILITIES)
        return {
            'id': i,
            'facility': facility['id'],
            'fug': random.choice(facility['fugs']),
            'timestamp': (datetime.utcnow() - timedelta(days=random.uniform(0, 30.44*window))).strftime('%Y-%m-%dT%H:%M:%S'),
            'satisfied': tf(),
            type: value,
            'message': random.choice(messages) if random.random() < .5 else None,
        }

    reports = [mk_report(i + 1) for i in range(n)]
    with open(path, 'w') as f:
        json.dump(reports, f)

def api_main(request):
    payload = {
        'stats': main_dashboard_stats(),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def main_dashboard_stats():
    data = load_reports()

    facilities = map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])

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
        'facilities': FACILITIES,
        'monthly': detail_stats(site),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def detail_stats(facility_id):
    data = load_reports()

    facilities = map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])

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




