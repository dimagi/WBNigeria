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

from aremind.apps.utils.functional import map_reduce

import shared as u
from apps.dashboard.models import FadamaReport, ReportComment

from rapidsms.contrib.locations.models import Location

def get_facilities():
    facs = u.get_facilities('fca')
    for f in facs:
        f['fugs'] = sorted(fug.name for fug in Location.objects.filter(type__slug='fug', parent_id=f['id']))
    return facs

def facilities_by_id():
    return map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])

def extract_report(r):
    data = u.extract_report(r)
    fug_id = data['facility']
    fug = Location.objects.get(id=fug_id)
    data['fug'] = fug.name
    data['facility'] = fug.parent_id
    return data

def load_reports(state=None, anonymize=True):
    reports = [extract_report(r) for r in FadamaReport.objects.all().select_related()]

    facs = facilities_by_id()
    reports = [r for r in reports if state is None or state == facs[r['facility']]['state']]

    def _ts(r):
        return datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')

    for r in reports:
        if not anonymize:
            r['_contact'] = r['contact']
        u.anonymize_contact(r)
        r['month'] = _ts(r).strftime('%b %Y')
        r['_month'] = _ts(r).strftime('%Y-%m')
        r['thread'] = [c.json() for c in sorted(ReportComment.objects.filter(report__id=r['id']), key=lambda c: c.date)]
        r['display_time'] = _ts(r).strftime('%d/%m/%y %H:%M')
        r['site_name'] = facs[r['facility']]['name']

    reports_by_contact = map_reduce((r for r in reports if not r['proxy']), lambda r: [(r['contact'], r)])
    print reports_by_contact

    for r in reports:
        r['from_same'] = [k['id'] for k in reports_by_contact.get(r['contact'], []) if k != r and abs(_ts(r) - _ts(k)) <= settings.RECENT_REPORTS_FROM_SAME_PHONE_WINDOW]

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


def message_report_beneficiary(report, message_text):
    "Send a message to a user based on a report."
    template = u'{0} {1}'.format(communicator_prefix(), message_text)
    message = OutgoingMessage(connection=report.reporter, template=template)
    router = Router()
    router.outgoing(message)


