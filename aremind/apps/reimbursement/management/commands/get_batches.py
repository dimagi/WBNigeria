from aremind.apps.reimbursement import views
from django.core.management.base import BaseCommand
import logging

class Command(BaseCommand):
    "Get new messages to be reimbursed"

    help = u'Get new messages and calculate amounts to be reimbursed'

    def handle(self, *args, **options):
        res = views.next_batch()
        logging.info('%s reimbursements in batch'%res)
        print "done with batches"
