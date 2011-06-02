import datetime
import logging

from django.db import models
from apps.patients.models import Patient

logger = logging.getLogger('wisepill.models')

class WisepillMessage(models.Model):
    """Record of a message received from a wisepill device.
    Keep the raw message, and parse out the info we want
    into individual fields."""

    # The raw message received
    sms_message = models.CharField(max_length=160)
    # when received
    time_received = models.DateTimeField(auto_now_add=True)

    # Data parsed from message
    LIVE_EVENT = 2
    DELAYED_EVENT = 3
    MESSAGE_TYPE_CHOICES = (
        (LIVE_EVENT, 'Live event'),
        (DELAYED_EVENT, 'Delayed event'),
        )
    message_type = models.SmallIntegerField(choices=MESSAGE_TYPE_CHOICES, default=LIVE_EVENT)
    msisdn = models.CharField(max_length=12,blank=True)
    # the timestamp that was in the message
    timestamp = models.DateTimeField(blank=True)

    # the patient who has this device, if known
    patient = models.ForeignKey(Patient, related_name='wisepill_messages', blank=True,null=True)

    def __unicode__(self):
        return u"%s %s" % (self.timestamp, self.msisdn)

    def is_delayed(self):
        """Whether this was a delayed message"""
        return self.message_type == WisepillMessage.DELAYED_EVENT

    def save(self, *args, **kwargs):
        # First time only, if we have the raw message, parse it out
        # into the other fields
        if not self.pk and self.sms_message is not None and self.sms_message != '':
            self._parse_message()
            # and set the patient field based on the msisdn
            self.set_patient()
        super(WisepillMessage,self).save(*args,**kwargs)

    def set_patient(self):
        """Point the patient field at the right patient, if possible.
        (Does not save)"""
        # try to find the patient
        patients = Patient.objects.filter(wisepill_msisdn = self.msisdn)
        if patients.count() == 1:
            self.patient = patients[0]
        else:
            logger.debug("Unable to find patient for MSISDN %s" % self.msisdn)

    def _parse_message(self):
        """Parse the raw message into the other fields.
        (Only the other fields that we currently care about.)
        (Does not save.)

Example message:

@=03,CN=256771413470,SN=357077005471753,T=190509060959,S=20,B=3800,PC=1,U= balance is UGX 15893. Yo,M=1,CE=0

@=<message type: 02 = live event, 03 = delayed event>,
CN=<MSISDN>,
SN=<Device Serial Number>,
T=<DateTime: DDMMYYHHMMSS>
S=<Signal Strength: 0-31, 99>,
B=<Battery strength (mV)>,
PC=<Puff Count: Not Used>,
U=<USSD Response: Network response to configured USSD command>,
M=<Medication compartment: Value= 1 for Wisepill portable dispenser>,
CE=<Parameter Not used: value = 0>
CR/LF

Newer devices seem to change @= to AT=.

"""
        parts = self.sms_message.split(",")
        values = {}
        for part in parts:
            key,value = part.split("=",1)
            values[key] = value
        # grab the parts we want
        if '@' in values:
            self.message_type = int(values['@'])
        elif 'AT' in values:
            self.message_type = int(values['AT'])
        self.msisdn = values['CN']
        # datetime format=DDMMYYHHMMSS
        t = values['T']
        (dd,month,yy,hh,minute,ss) = [int(x) for x in (t[0:2],t[2:4],t[4:6],t[6:8],t[8:10],t[10:12])]
        yy += 2000  # Y2K!
        self.timestamp = datetime.datetime(yy,month,dd,hh,minute,ss)
