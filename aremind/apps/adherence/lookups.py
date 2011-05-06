from selectable.base import ModelLookup
from selectable.registry import registry

from aremind.apps.adherence.models import Reminder


class ReminderLookup(ModelLookup):
    model = Reminder
    search_field = 'frequency__icontatins'

registry.register(ReminderLookup)
