from celery.task import Task
from celery.registry import tasks

from threadless_router.router import Router

from aremind.apps.adherence.models import Feed
from aremind.apps.adherence.app import start_tree_for_all_patients


class ReminderSchedulerTask(Task):
    def run(self):
        router = Router()
        app = router.get_app("aremind.apps.adherence")
        app.cronjob()


tasks.register(ReminderSchedulerTask)


class FeedUpdatesTask(Task):
    def run(self):
        return Feed.objects.fetch_feeds()
        

tasks.register(FeedUpdatesTask)

class KickoffAdherenceSurveysTask(Task):
    def run(self):
        start_tree_for_all_patients()

tasks.register(KickoffAdherenceSurveysTask)
