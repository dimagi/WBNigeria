from django.core.management.base import NoArgsCommand

from aremind.apps.adherence.models import Feed


class Command(NoArgsCommand):
    help = 'Fetches the latest feed data for active feeds.'

    def handle_noargs(self, **options):
        count = Feed.objects.fetch_feeds()
        self.stdout.write('Successfully fetched %s entries.\n' % count)
