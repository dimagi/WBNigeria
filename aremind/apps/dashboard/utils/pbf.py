import json
from datetime import datetime

from django.conf import settings

from aremind.apps.utils.functional import map_reduce


FACILITIES = [
    {'id': 1, 'name': 'Wamba General Hospital', 'lat': 8.936, 'lon': 8.6057},
    {'id': 2, 'name': 'Arum Health Center', 'lat': 9.0994, 'lon': 8.65049},
    {'id': 3, 'name': 'Mangar Health Center', 'lat': 9.0667, 'lon': 8.73339},
    {'id': 4, 'name': 'Gitta Health Center', 'lat': 9.0458, 'lon': 8.49866},
    {'id': 5, 'name': 'Nakere Health Center', 'lat': 8.8087, 'lon': 8.53412},
    {'id': 6, 'name': 'Konvah Health Center', 'lat': 8.8668, 'lon': 8.81727},
    {'id': 7, 'name': 'Wayo Health Center', 'lat': 8.8047, 'lon': 8.73558},
    {'id': 8, 'name': 'Wamba West Health Center', 'lat': 8.8396, 'lon': 8.6311},
    {'id': 9, 'name': 'Wamba East Health Center (Model Clinic)', 'lat': 8.9047, 'lon': 8.7032},
    {'id': 10, 'name': 'Kwara Health Center', 'lat': 8.9967, 'lon': 8.7492},
    {'id': 11, 'name': 'Jimiya Health Center', 'lat': 8.9485, 'lon': 8.8334},
]


WAIT_BUCKETS = [(2, '<2'), (4, '2-4'), (None, '>4')]


def process_raw_report(report):
    "Map report to a month/year group and include wait time bucket."
    ts = datetime.strptime(report['timestamp'], '%Y-%m-%dT%H:%M:%S')
    report['month'] = ts.strftime('%b %Y')
    report['_month'] = ts.strftime('%Y-%m')
    for thresh, label in WAIT_BUCKETS:
        if thresh is None or report['waiting_time'] < thresh:
            report['wait_bucket'] = label
            break
    return report


def load_reports(path=settings.DASHBOARD_SAMPLE_DATA['pbf']):
    with open(path) as f:
        reports = json.load(f)
    return map(process_raw_report, reports)


def main_dashboard_stats():
    data = load_reports()

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
    data = load_reports()

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
