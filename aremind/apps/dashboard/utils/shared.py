
import hashlib

from rapidsms.contrib.locations.models import Location


def extract_report(r):
    data = r.content
    data.update({
            'id': r.id,
            'satisfied': r.satisfied,
            'contact': r.reporter.identity,
            'facility': r.site.id,
            'message': r.freeform,
            'proxy': r.proxy,
            'timestamp': r.timestamp.strftime('%Y-%m-%dT%H:%M:%S'),
        })
    return data

def get_facilities(type):
    def mk_fac(f):
        return {
            'id': f.id,
            'name': f.name,
            'lat': float(f.point.latitude),
            'lon': float(f.point.longitude),
            'state': Location.objects.get(id=f.parent_id).slug,
        }
    return [mk_fac(f) for f in Location.objects.filter(type__slug=type)]

def anonymizer(val, len=12):
    salt = 'utbzembsanxp0'
    return hashlib.sha1(salt + val).hexdigest()[:len]

def anonymize_contact(r, anonfunc=anonymizer):
    r['contact'] = anonfunc(r['contact'])

