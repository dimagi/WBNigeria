import json
import random
from datetime import datetime
import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Backend, Connection
from threadless_router.router import Router

from aremind.apps.dashboard.models import ReportComment
from aremind.apps.utils.functional import map_reduce



def facilities_by_id():
    return map_reduce(FACILITIES, lambda e: [(e['id'], e)], lambda v: v[0])

def anonymizer(val, len=12):
    salt = 'utbzembsanxp0'
    return hashlib.sha1(salt + val).hexdigest()[:len]

def anonymize_contact(r, anonfunc=anonymizer):
    r['contact'] = anonfunc(r['contact'])

def load_reports(state=None, path=settings.DASHBOARD_SAMPLE_DATA['fadama'], anonymize=True):
    with open(path) as f:
        reports = json.load(f)

    facs = facilities_by_id()
    reports = [r for r in reports if state is None or state == facs[r['facility']]['state']]

    comments = ReportComment.objects.all() # TODO: not scalable
    by_report = map_reduce(comments, lambda c: [(c.report_id, c)])

    def _ts(r):
        return datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')

    for r in reports:
        if not anonymize:
            r['_contact'] = r['contact']
        anonymize_contact(r)
        r['month'] = _ts(r).strftime('%b %Y')
        r['_month'] = _ts(r).strftime('%Y-%m')
        r['thread'] = [c.json() for c in sorted(by_report.get(r['id'], []), key=lambda c: c.date)]
        r['display_time'] = _ts(r).strftime('%d/%m/%y %H:%M')
        r['site_name'] = facs[r['facility']]['name']

    reports_by_contact = map_reduce((r for r in reports if not r['proxy']), lambda r: [(r['contact'], r)])
    for r in reports:
        r['from_same'] = [k['id'] for k in reports_by_contact[r['contact']] if k != r and abs(_ts(r) - _ts(k)) <= settings.RECENT_REPORTS_FROM_SAME_PHONE_WINDOW]

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

def logs_for_contact(contact):
    return sorted([r for r in load_reports() if r['contact'] == contact and not r['proxy']], key=lambda r: r['timestamp'], reverse=True)


def communicator_prefix():
    return _('From fadama:')


def message_report_beneficiary(report_id, message_text):
    "Send a message to a user based on a report."
    connection = _get_connection_from_report(report_id)
    template = u'{0} {1}'.format(communicator_prefix(), message_text)
    message = OutgoingMessage(connection=connection, template=template)
    router = Router()
    router.outgoing(message)


