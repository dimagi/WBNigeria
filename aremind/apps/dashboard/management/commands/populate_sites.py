import csv
import os.path
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rapidsms.models import Backend, Connection
from rapidsms.contrib.locations.models import Location, Point
from smsforms.models import DecisionTrigger
from touchforms.formplayer.models import XForm

class Command(BaseCommand):
    "Populate Fadama and PBF sites"

    help = u'Populate Fadama and PBF sites in database. Run after all other fixture imports.'

    def handle(self, *args, **options):
        if not Location.objects.filter(type__slug='state'):
            print 'no state locations defined; did you import the other fixtures yet?'
            return

        fixture_path = os.path.join(settings.PROJECT_PATH, 'apps', 'dashboard', 'fixtures', 'sites.csv')
        populate(fixture_path)

def populate(path):
    with open(path) as f:
        data = csv.DictReader(f)
        for row in data:
            populate_site(row)

def populate_site(row):
    for k, v in row.items():
        if v == '':
            row[k] = None

    if row['latitude']:
        row['point'] = Point.objects.get_or_create(latitude=row['latitude'], longitude=row['longitude'])[0]
    del row['latitude']
    del row['longitude']

    Location(**row).save()

    if row['keyword']:
        # get state
        state = Location.objects.get(id=row['id'])
        while state.type_id != 'state':
            state = Location.objects.get(id=state.parent_id)

        site_type = {
            'fug': 'fadama',
            'fca': 'fadama',
            'clinic': 'pbf',
        }[row['type_id']]
        # TODO this could fail when multiple form versions are around
        form = XForm.objects.get(namespace=settings.DECISION_TREE_FORMS[site_type])

        DecisionTrigger(
            xform=form,
            trigger_keyword=row['keyword'],
            context_data=json.dumps({
                    'site_id': str(row['id']),
                    'state_name': state.name,
                    '_select_text_mode': 'none',
                })
        ).save()
