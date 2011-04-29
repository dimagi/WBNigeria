from celery.task import Task
from celery.registry import tasks

from threadless_router.router import Router


class ReminderSchedulerTask(Task):
    def run(self):
        router = Router()
        app = router.get_app("aremind.apps.adherence")
        app.cronjob()

tasks.register(ReminderSchedulerTask)
