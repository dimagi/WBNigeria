import json
from datetime import datetime

from django.conf import settings

from aremind.apps.utils.functional import map_reduce
import shared as u

from apps.dashboard.models import PBFReport, ReportComment

def load_reports():
    # TODO: filtering by state

    facilities = map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])
    reports = [u.extract_report(r) for r in PBFReport.objects.all().select_related()]
    comments = map_reduce(ReportComment.objects.filter(pbf_report__isnull=False), lambda c: [(c.pbf_report_id, c)])

    wait_buckets = [(2, '<2'), (4, '2-4'), (None, '>4')]

    for r in reports:
        u.anonymize_contact(r)
        ts = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')
        r['thread'] = [c.json() for c in sorted(comments.get(r['id'], []), key=lambda c: c.date)]
        r['month'] = ts.strftime('%b %Y')
        r['_month'] = ts.strftime('%Y-%m')
        r['display_time'] = datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S').strftime('%d/%m/%y %H:%M')
        r['site_name'] = facilities[r['facility']]['name'] if r['for_this_site'] else r['site_other']
        if r['waiting_time'] is not None:
            for thresh, label in wait_buckets:
                if thresh is None or r['waiting_time'] < thresh:
                    r['wait_bucket'] = label
                    break
        else:
            r['wait_bucket'] = None

    return reports

def get_facilities():
    return u.get_facilities('clinic')

def main_dashboard_stats():
    data = load_reports()

    facilities = map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])

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
            'by_clinic': [[facilities.get(k), v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    by_month = map_reduce(data, lambda r: [((r['month'], r['_month']), r)])
    stats = [month_stats(by_month.get(month_key, []), month_key) for month_key in u.iter_report_range(data)]
    return sorted(stats, key=lambda e: e['_month'])

def detail_stats(facility_id):
    data = load_reports()

    facilities = map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])

    def fac_filter(r, facility_id):
        if facility_id is None:
            return True
        elif facility_id == 999: # 'other' sites
            return r['facility'] is None
        else:
            return r['facility'] == facility_id

    filtered_data = [r for r in data if fac_filter(r, facility_id)]

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
            'clinic_totals': [[facilities.get(k), v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    by_month = map_reduce(filtered_data, lambda r: [((r['month'], r['_month']), r)])
    stats = [month_detail(by_month.get(month_key, []), month_key) for month_key in u.iter_report_range(filtered_data)]
    return sorted(stats, key=lambda e: e['_month'])

def log_single(report_id):
    return [r for r in load_reports() if r['id'] == report_id]
