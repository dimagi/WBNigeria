import datetime

from django.core import management

from celery.task import PeriodicTask
from celery.registry import tasks

from threadless_router.router import Router


class GenerateNotificationsTask(PeriodicTask):
    run_every = datetime.timedelta(days=1)

    def run(self):
        management.call_command('trigger_alerts')


tasks.register(GenerateNotificationsTask)
