from django.db import models


class LocationExtra(models.Model):
    """ """
    name = models.CharField(max_length=100, null=True, blank=True,
            help_text="The full name of this Location.")
    slug = models.SlugField(max_length=50, null=True, blank=True,
            help_text="A unique identifier for this Location.")

    class Meta:
        abstract = True 
