from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def dashboard(request):
    return render(request, 'dashboard/pbf/dashboard.html')


@login_required
def reports(request):
    return render(request, 'dashboard/pbf/reports.html')


@login_required
def site_detail(request, pk):
    return render(request, 'dashboard/pbf/site_detail.html')


import json
import random
from datetime import datetime, timedelta
import collections

FACILITIES = [
    {'id': 1, 'name': 'Wamba General Hospital', 'lat': 9.2, 'lon': 7.18},
    {'id': 2, 'name': 'Arum Health Center', 'lat': 9.1, 'lon': 6.02},
    {'id': 3, 'name': 'Mangar Health Center', 'lat': 4.97, 'lon': 8.35},
    {'id': 4, 'name': 'Gitta Health Center', 'lat': 6.47, 'lon': 7.55},
    {'id': 5, 'name': 'Nakere Health Center', 'lat': 12.17, 'lon': 6.7},
    {'id': 6, 'name': 'Konvah Health Center', 'lat': 7.43, 'lon': 3.9},
    {'id': 7, 'name': 'Wayo Health Center', 'lat': 8.48, 'lon': 4.58},
    {'id': 8, 'name': 'Wamba West Health Center', 'lat': 9.87, 'lon': 8.9},
    {'id': 9, 'name': 'Wamba East Health Center (Model Clinic)', 'lat': 10.6, 'lon': 7.45},
    {'id': 10, 'name': 'Kwara Health Center', 'lat': 12.05, 'lon': 8.53},
    {'id': 11, 'name': 'Jimiya Health Center', 'lat': 6.58, 'lon': 3.33},
]

def load_reports(path):
    with open(path) as f:
        reports = json.load(f)

    wait_buckets = [(2, '<2'), (4, '2-4'), (None, '>4')]

    for r in reports:
        ts = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')
        r['month'] = ts.strftime('%b %Y')
        r['_month'] = ts.strftime('%Y-%m')
        for thresh, label in wait_buckets:
            if thresh is None or r['waiting_time'] < thresh:
                r['wait_bucket'] = label
                break

    return reports

def make_reports(path, n):
    def mk_report(i):
        messages = [
            'wait too long doctor no come',
            'waiting room too dirty',
            'no medicine',
        ]

        def tf():
            return (random.random() < .5)

        return {
            'id': i,
            'facility': random.choice(FACILITIES)['id'],
            'timestamp': (datetime.utcnow() - timedelta(days=random.uniform(0, 180))).strftime('%Y-%m-%dT%H:%M:%S'),
            'satisfied': tf(),
            'waiting_time': random.randint(0, 7),
            'staff_friendliness': tf(),
            'price_display': tf(),
            'drug_availability': tf(),
            'cleanliness': tf(),
            'message': random.choice(messages) if random.random() < .3 else None,
        }

    reports = [mk_report(i + 1) for i in range(n)]
    with open(path, 'w') as f:
        json.dump(reports, f)

TEST_DATA = '/tmp/data'

def api_main(request):
    payload = {
        'stats': main_dashboard_stats(),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def api_detail(request):
    _site = request.GET.get('site')
    site = int(_site) if _site else None

    payload = {
        'facilities': FACILITIES,
        'monthly': detail_stats(site),
    }
    return HttpResponse(json.dumps(payload), 'text/json')

def main_dashboard_stats():
    data = load_reports(TEST_DATA)

    facilities = map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])

    def month_stats(data, label):
        return {
            'total': len(data),
            'satisfaction': map_reduce(data, lambda r: [(r['satisfied'],)], len),
            'by_category': dict((k, len([r for r in data if r[k]])) for k in (
                    'waiting_time',
                    'staff_friendliness',
                    'price_display',
                    'drug_availability',
                    'cleanliness',
                )),
            'by_clinic': [[facilities[k], v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    return sorted(map_reduce(data, lambda r: [((r['month'], r['_month']), r)], month_stats).values(), key=lambda e: e['_month'])

def detail_stats(facility_id):
    data = load_reports(TEST_DATA)

    facilities = map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])

    filtered_data = [r for r in data if facility_id is None or r['facility'] == facility_id]
    for r in filtered_data:
        r['display_time'] = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%y %H:%M')
        r['site_name'] = facilities[r['facility']]['name']

    LIMIT = 50
    def month_detail(data, label):
        return {
            'total': len(data),
            'logs': sorted(data, key=lambda r: r['timestamp'], reverse=True)[:LIMIT],
            'stats': dict((k, map_reduce(data, lambda r: [(r[k],)], len)) for k in (
                'satisfied',
                'wait_bucket',
                'staff_friendliness',
                'price_display',
                'drug_availability',
                'cleanliness',
            )),
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
