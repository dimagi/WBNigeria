from django.db import models

# this doesn't seem to be taking effect

class LocationExtra(models.Model):
    """ """
    pbf_category = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True 
