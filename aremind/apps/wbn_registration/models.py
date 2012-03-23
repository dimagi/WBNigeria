from django.db import models
from rapidsms.models import Contact, Connection

# Create your models here.

class WBUser(models.Model):
    connection = models.ForeignKey(Connection)
    is_registered = models.BooleanField(default=False)
    location_code = models.CharField(max_length=4)