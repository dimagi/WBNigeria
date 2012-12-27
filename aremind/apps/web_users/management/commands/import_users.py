import csv
import os.path
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User, Permission
from rapidsms.models import Backend, Contact, Connection
from rapidsms.contrib.locations.models import Location, Point
from smsforms.models import DecisionTrigger
from touchforms.formplayer.models import XForm

PERMS = ('pbf_view', 'fadama_view', 'supervisor')

class Command(BaseCommand):
    "Populate Users"

    help = u'Populate users from csv file'

    def handle(self, *args, **options):
        if not Location.objects.filter(type__slug='state'):
            print 'no state locations defined; did you import the other fixtures yet?'
            return

        #check that the required permissions are defined
        for perm in PERMS:
            try:
                Permission.objects.get(codename=perm)
            except Permission.DoesNotExist:
                print 'run data migrations on dashboard app to install %s' % perm
                return

        try:
            path = args[0]
        except IndexError:
            print 'specify a *.csv file containing the user data'
            return

        populate(args[0])

def populate(path):
    with open(path) as f:
        data = csv.DictReader(f)
        for row in data:
            populate_user(row)

def populate_user(row):
    for k, v in row.items():
        if v == '':
            del row[k]

    NON_REQUIRED_FIELDS = ['email', 'supervisor', 'phone']

    for k, v in row.iteritems():
        if v is None and k not in NON_REQUIRED_FIELDS:
            print '%s is required' % k
            return

    try:
        User.objects.get(username=row['username'])
        print 'user %s already exists' % row['username']
        return
    except User.DoesNotExist:
        pass

    ALLOWED_STATES = ('fct', 'nasawara', 'national')
    if not row['state'] in ALLOWED_STATES:
        print 'state must be one of: %s' % ', '.join(ALLOWED_STATES)
        return

    ALLOWED_PROGRAMS = ('pbf', 'fadama', 'both')
    if not row['program'] in ALLOWED_PROGRAMS:
        print 'program must be one of: %s' % ', '.join(ALLOWED_PROGRAMS)
        return

    PROGRAM_PERMS = {
        'pbf': 'pbf_view',
        'fadama': 'fadama_view',
    }
    perms = []
    if row['program'] == 'both':
        perms.extend(PROGRAM_PERMS.values())
    else:
        perms.append(PROGRAM_PERMS[row['program']])

    is_supervisor = (row.get('supervisor', '').lower() in ('y', 'yes', 'x'))
    if is_supervisor:
        perms.append('supervisor')

    def add_perm(u, perm_name):
        u.user_permissions.add(Permission.objects.get(codename=perm_name))

    u = User()
    u.username = row['username']
    u.first_name = row['first name']
    u.last_name = row['last name']
    u.email = row.get('email', 'nobody@nowhere.ng')
    u.set_password(row['password'])
    u.save()

    for p in perms:
        add_perm(u, p)
    u.save()

    try:
        contact = Contact.objects.get(user__username=row['username'])
        return
    except Contact.DoesNotExist:
        pass

    if row['state'] == 'national':
        loc = Location.objects.get(slug='nigeria')
    else:
        loc = Location.objects.get(type__slug='state', slug=row['state'])

    c = Contact()
    c.name = '%s %s' % (u.first_name, u.last_name)
    c.first_name = u.first_name
    c.last_name = u.last_name
    c.email = row.get('email', '')
    c.user = u
    c.location = loc
    c.save()

    backend = Backend.objects.get(name='httptester')

    if row.get('phone'):
        conn = Connection()
        conn.backend = backend
        conn.identity = row['phone']
        conn.contact = c
        conn.save()
