import json
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse

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
