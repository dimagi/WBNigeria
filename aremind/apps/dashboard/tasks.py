from django.core import management

from celery.task import Task
from celery.registry import tasks

from threadless_router.router import Router


class GenerateNotificationsTask(Task):
    
    def run(self):
        management.call_command('trigger_alerts')


tasks.register(GenerateNotificationsTask)
