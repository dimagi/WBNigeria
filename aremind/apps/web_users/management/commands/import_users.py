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

ALLOWED_PERMS = ('pbf_view', 'fadama_view')

class Command(BaseCommand):
    "Populate Users"

    help = u'Populate users from csv file'

    def handle(self, *args, **options):
        if not Location.objects.filter(type__slug='state'):
            print 'no state locations defined; did you import the other fixtures yet?'
            return

        #check that the ALLOWED_PERMS exist
        for perm in ALLOWED_PERMS:
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
        #import pdb;pdb.set_trace()
        for row in data:
            populate_user(row)

def populate_user(row):
    for k, v in row.items():
        if v == '':
            del row[k]

    NON_REQUIRED_FIELDS = ['email', 'perm']

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

    if 'perm' in row and not row['perm'] in ALLOWED_PERMS:
        print 'perm must be one of: %s' % ', '.join(ALLOWED_PERMS)
        return

    if 'perm' in row:
        perm = Permission.objects.get(codename=row['perm'])
    else:
        perm = None

    u = User()
    u.username = row['username']
    u.first_name = row['first name']
    u.last_name = row['last name']
    u.email = row.get('email', 'nobody@nowhere.ng')
    u.set_password(row['password'])
    u.save()

    if perm:
        u.user_permissions.add(perm)

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
