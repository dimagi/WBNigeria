from django.contrib.auth.models import User
from django.db import models

from rapidsms.contrib.locations.models import Location


class ContactExtra(models.Model):
    """Extensions to the RapidSMS contact model to locate a user."""
    user = models.ForeignKey(User, null=True, blank=True, unique=True)
    location = models.ForeignKey(Location, null=True, blank=True)

    class Meta:
        abstract = True
