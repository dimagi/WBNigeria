from django.db import models
from rapidsms.models import Connection

class XFormsSession(models.Model):
    connection = models.ForeignKey(Connection, related_name='xform_sessions')
    session_id = models.CharField(max_length=200,null=True,blank=True)
    start_time = models.DateTimeField(blank=True, null=True)
    touch_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    current_response = models.CharField(max_length=500, null=True, blank=True)
    possible_answers = models.CharField(max_length=255, null=True, blank=True, help_text="Possible answers to the current question (leave blank for freeform") #Used for (1)Select questions to keep track of possible answers
    error_msg = models.CharField(max_length=255, null=True, blank=True, help_text="Error message last received, if any")
    started = models.BooleanField(default=False, help_text="Has this Session been started?")
    ended = models.BooleanField(default=False, help_text="Has this session ended?")




