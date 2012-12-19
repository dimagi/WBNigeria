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
from apps.dashboard.models import FadamaReport, ReportComment, ReportCommentView

from rapidsms.contrib.locations.models import Location

def get_facilities():
    facs = u.get_facilities('fca')
    fugs_by_fca = map_reduce(Location.objects.filter(type__slug='fug'), lambda f: [(f.parent_id, f)])
    for f in facs:
        f['fugs'] = sorted(fug.name for fug in fugs_by_fca.get(f['id'], []))
    return facs

def facilities_by_id():
    return map_reduce(get_facilities(), lambda e: [(e['id'], e)], lambda v: v[0])

def load_reports(user=None, state=None, anonymize=True):
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
    comments = map_reduce(ReportComment.objects.filter(fadama_report__isnull=False), lambda c: [(c.fadama_report_id, c)])

    def _ts(r):
        return datetime.strptime(r['timestamp'], '%Y-%m-%dT%H:%M:%S')

    views = []
    if user:
        views = ReportCommentView.objects.filter(user=user)\
                                         .values_list('report_comment', flat=True)
    def _get_json(comment):  # Add whether or not the comment has been viewed.
        json = comment.json()
        json.update({'viewed': comment.pk in views if user else None})
        return json

    for r in reports:
        if not anonymize:
            r['_contact'] = r['contact']
        u.anonymize_contact(r)
        r['month'] = _ts(r).strftime('%b %Y')
        r['_month'] = _ts(r).strftime('%Y-%m')
        r['thread'] = [_get_json(c) for c in sorted(comments.get(r['id'], []), key=lambda c: c.date)]
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


def main_dashboard_stats(user=None, state=None):
    data = load_reports(state=state, user=user)

    facilities = facilities_by_id()

    def month_stats(data, label):
        return {
            'total': len(data),
            'satisfaction': map_reduce(data, lambda r: [(r['satisfied'],)], len),
            'by_category': dict((k, len([r for r in data if k in r])) for k in COMPLAINT_TYPES),
            'by_clinic': [[facilities.get(k), v] for k, v in map_reduce(data, lambda r: [(r['facility'],)], len).iteritems()],
            'month': label[0],
            '_month': label[1],
        }

    by_month = map_reduce(data, lambda r: [((r['month'], r['_month']), r)])
    stats = [month_stats(by_month.get(month_key, []), month_key) for month_key in u.iter_report_range(data)]
    return sorted(stats, key=lambda e: e['_month'])

def detail_stats(facility_id, user=None, state=None):
    data = load_reports(user=user, state=state)

    def fac_filter(r, facility_id):
        if facility_id is None:
            return True
        elif facility_id == -999: # 'other' sites
            return r['facility'] is None
        else:
            return r['facility'] == facility_id
    filtered_data = [r for r in data if fac_filter(r, facility_id)]

    facilities = facilities_by_id()
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


