from django.db import models
from rapidsms.models import Contact

class XFormSurvey(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255) #Unclear if this should be a url or a path or what.
    stats_complete = models.IntegerField(max_length=6)
    stats_started = models.IntegerField(max_length=6)

class XFormsSession(models.Model):
    contact = models.ForeignKey(Contact, related_name='xform_sessions')
    session_id = models.CharField(max_length=200,null=True,blank=True)
    start_time = models.DateTimeField(blank=True, null=True)
    touch_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    form = models.ForeignKey(XFormSurvey)
    possible_answers = models.CharField(max_length=255, null=True, blank=True, help_text="Possible answers to the current question (leave blank for freeform") #Used for (1)Select questions to keep track of possible answers
    error_msg = models.CharField(max_length=255, null=True, blank=True, help_text="Error message last received, if any")
    started = models.BooleanField(default=False, help_text="Has this Session been started?")




