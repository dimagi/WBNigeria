from selectable.base import ModelLookup
from selectable.registry import registry

from aremind.apps.adherence.models import Reminder, Feed, QuerySchedule


class ReminderLookup(ModelLookup):
    model = Reminder
    search_field = 'frequency__icontatins'


registry.register(ReminderLookup)


class FeedLookup(ModelLookup):
    model = Feed
    search_field = 'name__icontatins'


registry.register(FeedLookup)

class QueryLookup(ModelLookup):
    model = QuerySchedule
    search_field = 'patients'

registry.register(QueryLookup)
