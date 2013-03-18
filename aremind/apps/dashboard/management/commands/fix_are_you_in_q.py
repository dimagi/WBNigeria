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
    def handle(self, *args, **options):
        triggers = DecisionTrigger.objects.all()

        for tr in triggers:
            data = json.loads(tr.context_data)

            loc = Location.objects.get(id=data['site_id'])
            if loc.type.slug not in ('fca', 'fug'):
                continue

            disp_name = loc.name
            if any(disp_name.lower().endswith(k) for k in ('fca', 'fug')):
                disp_name = disp_name[:-3].strip()

            if len(disp_name) > 50:
                disp_name = disp_name[:50-3] + '...'

            disp_name = '%s %s' % (disp_name, loc.type.slug.upper())

            data['site_name'] = disp_name
            tr.context_data = json.dumps(data)
            tr.save()


