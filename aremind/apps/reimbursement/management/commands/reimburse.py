from aremind.apps.reimbursement import views
from django.core.management.base import BaseCommand
import logging

class Command(BaseCommand):
    "Start reimbursement process"

    help = u'Start reimbursement process for all the networks'

    def handle(self, *args, **options):
        res = views.reimburse()
        logging.info('Reimbursement started for %s subscribers'%res)
