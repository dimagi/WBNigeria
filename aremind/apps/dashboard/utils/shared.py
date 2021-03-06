import hashlib
from rapidsms.contrib.locations.models import Location
from aremind.apps.utils.functional import map_reduce
from datetime import datetime
from rapidsms.models import Backend, Connection, Contact
from django.db.models import Q
from django.contrib.auth.models import User, Permission
from django.conf import settings

def extract_report(r):
    data = r.content
    data.update({
            'id': r.id,
            'satisfied': r.satisfied,
            'contact': r.reporter.identity,
            'reporting_facility': r.site.id,
            'facility': r.site.id if r.for_this_site else None,
            'for_this_site': r.for_this_site,
            'message': r.freeform,
            'proxy': r.proxy,
            'timestamp': r.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
            'can_contact': r.can_contact,
        })
    return data

# location.parent does not foreign key to location, so we can use this
# as a caching helper
def _fac_cache(type=None):
    if type:
        facs = Location.objects.filter(type__slug=type)
    else:
        facs = Location.objects.all()
    by_id = map_reduce(facs, lambda f: [(f.id, f)], lambda v: v[0])
    return lambda id: by_id.get(id)

def get_facilities(type):
    _parents = _fac_cache('state')
    def mk_fac(f):
        return {
            'id': f.id,
            'name': f.name,
            'lat': float(f.point.latitude),
            'lon': float(f.point.longitude),
            'state': _parents(f.parent_id).slug,
        }
    return [mk_fac(f) for f in Location.objects.filter(type__slug=type).select_related('point')]

def anonymizer(val, len=12):
    salt = 'utbzembsanxp0'
    return hashlib.sha1(salt + val).hexdigest()[:len]

def anonymize_contact(r, anonfunc=anonymizer):
    r['contact'] = anonfunc(r['contact'])

def get_user_state(user):
    try:
        contact = user.contact_set.all()[0]
    except IndexError:
        return None

    loc = contact.location
    if not loc:
        return None

    if loc.type.slug != 'state':
        return None

    return loc.slug

def reports_range(data):
    if data:
        return min(r['_month'] for r in data), max(r['_month'] for r in data)
    else:
        return None, None

def month_key(timestamp_str):
    ts = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
    return {
        'month': ts.strftime('%b %Y'),
        '_month': ts.strftime('%Y-%m'),
    }

def iter_report_range(data):
    if not data:
        return

    def to_month_num(key):
        y, m = [int(k) for k in key.split('-')]
        return 12 * y + (m - 1)

    def to_key(month_num):
        y = month_num // 12
        m = month_num % 12 + 1
        return (
            datetime(y, m, 1).strftime('%b %Y'),
            '%04d-%02d' % (y, m),
        )

    _min, _max = reports_range(data)
    for i in range(to_month_num(_min), to_month_num(_max) + 1):
        yield to_key(i)

def get_taggable_contacts(program, state, user):
    """
    Returns a map of location id to location name and the contacts in that
    location, for all locationsin the path of the state (or any location, if
    no state is provided.
    """

    def is_program_user(u):
        def program_member(program):
            return u.has_perm('dashboard.%s_view' % program)

        all_programs = ('pbf', 'fadama')
        # check that user is ONLY a member of the program at hand -- this filters out
        # supervisory accounts like worldbank (member of all programs)
        return program_member(program) and all(not program_member(p) for p in all_programs if p != program)

    def get_state_users(state):
        if state is None:
            criteria = {'location__slug': 'nigeria'}
        else:
            criteria = {'location__type__slug': 'state', 'location__slug': state}

        users = Contact.objects.filter(**criteria).select_related()
        for u in users:
            if is_program_user(u.user) and user.id != u.user.id:
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


def get_users_by_program(program):
    codename = '{0}_view'.format(program)
    perm = Permission.objects.filter(content_type__app_label='dashboard', codename=codename)
    superuser = Q(is_superuser=True)
    group_perm = Q(groups__permissions=perm)
    user_perm = Q(user_permissions=perm)
    return User.objects.filter(superuser | group_perm | user_perm)






def network_for_number(phone):
    #import pdb;pdb.set_trace()
    #try:
    #    backend = Connection.objects.get(identity=phone).backend.name
    #    return settings.INSTALLED_BACKENDS[backend]['sendsms_params']['modem']
    #except Exception:
    if phone.startswith('+'):
        phone = phone[1:]

    for prefix, network in settings.NETWORK_PREFIXES.iteritems():
        if phone.startswith(prefix):
            return network



