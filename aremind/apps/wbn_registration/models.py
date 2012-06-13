from django.db import models
from rapidsms.models import Contact, Connection

# Create your models here.

class WBUser(models.Model):
    connection = models.ForeignKey(Connection)
    is_registered = models.BooleanField(default=False, help_text="Has the user confirmed their registration+location?")
    location_code = models.CharField(max_length=255, help_text="A four digit location code indicating the geographical location of the user")
    survey_question_ans = models.CharField(max_length=255, null=True, blank=True, help_text="The answer the user gives to the post-registration-survey")
    want_more_surveys = models.BooleanField(default=False, help_text="Is the user willing to participate in more surveys?")
    date_registered = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return 'Connection: %s, Is Registered: %s, Location Code: %s'  % (self.connection, self.is_registered, self.location_code)
