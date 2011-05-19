import datetime
import logging

from django.db import models

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
    message_type = models.SmallIntegerField(choices=MESSAGE_TYPE_CHOICES,blank=True)
    msisdn = models.CharField(max_length=12,blank=True)
    # the timestamp that was in the message
    timestamp = models.DateTimeField(blank=True)

    def __unicode__(self):
        return u"%s %s" % (self.timestamp, self.msisdn)

    def is_delayed(self):
        """Whether this was a delayed message"""
        return self.message_type == DELAYED_EVENT

    def save(self, *args, **kwargs):
        self._parse_message()
        super(WisepillMessage,self).save(*args,**kwargs)

    def _parse_message(self):
        """Parse the raw message into the other fields.

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
"""
        parts = self.sms_message.split(",")
        values = {}
        for part in parts:
            key,value = part.split("=",1)
            values[key] = value
        # grab the parts we want
        self.message_type = int(values['@'])
        self.msisdn = values['CN']
        # datetime format=DDMMYYHHMMSS
        t = values['T']
        (dd,mm,yy,hh,mm,ss) = [int(x) for x in (t[0:2],t[2:4],t[4:6],t[6:8],t[8:10],t[10:12])]
        yy += 2000  # Y2K!
        self.timestamp = datetime.datetime(yy,mm,dd,hh,mm,ss)
