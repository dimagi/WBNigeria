from itertools import groupby
import json
import random
from datetime import datetime
import hashlib

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from rapidsms.messages.outgoing import OutgoingMessage
from rapidsms.models import Backend, Connection, Contact
from threadless_router.router import Router

from aremind.apps.utils.functional import map_reduce

import shared as u
from apps.dashboard.models import FadamaReport, ReportComment

from rapidsms.contrib.locations.models import Location

def get_facilities():
    facs = u.get_facilities('fca')
    fugs_by_fca = map_reduce(Location.objects.filter(type__slug='fug'), lambda f: [(f.parent_id, f)])
    for f in facs:
        f['fugs'] = sorted(fug.name for fug in fugs_by_fca.get(f['id'], []))
    return facs

def facilities_by_id():
    return map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])

def load_reports(state=None, anonymize=True):
    facs = facilities_by_id()
    fugs = u._fac_cache('fug')

    def extract_report(r):
        data = u.extract_report(r)
        loc_id = data['facility']

        fug = fugs(loc_id)
        if fug:
            data['fug'] = fug.name
            data['facility'] = fug.parent_id

        elif facs.get(loc_id):
            data['fug'] = None
            data['facility'] = loc_id

        else:
            data['fug'] = None
            data['facility'] = None

        return data

    reports = [extract_report(r) for r in FadamaReport.objects.all().select_related()]

    def filter_state(r, state):
        if state is None:
            return True
        else:
            reporting_fug = fugs(r['reporting_facility'])
            if reporting_fug:
                reporting_fca_id = reporting_fug.parent_id
            else:
                reporting_fca_id = r['reporting_facility']
            reporting_state = facs[reporting_fca_id]['state']
            return state == reporting_state

    reports = [r for r in reports if filter_state(r, state)]
    # todo: these should probably be loaded on-demand for individual reports
    comments = map_reduce(ReportComment.objects.all(), lambda c: [(c.report_id, c)])

    def _ts(r):
        return datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')

    for r in reports:
        if not anonymize:
            r['_contact'] = r['contact']
        u.anonymize_contact(r)
        r['month'] = _ts(r).strftime('%b %Y')
        r['_month'] = _ts(r).strftime('%Y-%m')
        r['thread'] = [c.json() for c in sorted(comments.get(r['id'], []), key=lambda c: c.date)]
        r['display_time'] = _ts(r).strftime('%d/%m/%y %H:%M')
        r['site_name'] = facs[r['facility']]['name'] if r['for_this_site'] else r['site_other']
 
    reports_by_contact = map_reduce((r for r in reports if not r['proxy']), lambda r: [(r['contact'], r)])

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
    'misc',
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
        'community', # combined FCA/FUG
        'facilitator',
        'desk',
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
    'misc': [
        'misc',
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

    by_month = map_reduce(data, lambda r: [((r['month'], r['_month']), r)])
    stats = [month_stats(by_month.get(month_key, []), month_key) for month_key in u.iter_report_range(data)]
    return sorted(stats, key=lambda e: e['_month'])

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
            'clinic_totals': [[facilities.get(k), v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    by_month = map_reduce(filtered_data, lambda r: [((r['month'], r['_month']), r)])
    stats = [month_detail(by_month.get(month_key, []), month_key) for month_key in u.iter_report_range(filtered_data)]
    return sorted(stats, key=lambda e: e['_month'])

def logs_for_contact(contact):
    return sorted([r for r in load_reports() if r['contact'] == contact and not r['proxy']], key=lambda r: r['timestamp'], reverse=True)

def log_single(report_id):
    return [r for r in load_reports() if r['id'] == report_id]

def communicator_prefix():
    return _('From fadama:')


def message_report_beneficiary(report, message_text):
    "Send a message to a user based on a report."
    template = u'{0} {1}'.format(communicator_prefix(), message_text)
    message = OutgoingMessage(connection=report.reporter, template=template)
    router = Router()
    router.outgoing(message)


def get_taggable_contacts(state, user):
    """
    Returns a map of location id to location name and the contacts in that
    location, for all locationsin the path of the state (or any location, if
    no state is provided.
    """

    def get_state_users(state):
        if state is None:
            criteria = {'location__slug': 'nigeria'}
        else:
            criteria = {'location__type__slug': 'state', 'location__slug': state}

        users = Contact.objects.filter(**criteria).select_related()
        for u in users:
            if user.id != u.user.id:
                yield {
                    'user_id': u.id,
                    'username': u.user.username,
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'state': state or 'national'
                }

    taggables = list(get_state_users(None))
    if state:
        taggables.extend(get_state_users(state))

    by_state = map_reduce(taggables, lambda u: [(u['state'], u)], lambda v, k: sorted(v, key=lambda u: (u['last_name'], u['first_name'])))
    by_state = [{'state': k, 'users': v} for k, v in by_state.iteritems()]
    by_state.sort(key=lambda e: 'zzzzz' if e['state'] == 'national' else e['state'])
    return by_state
