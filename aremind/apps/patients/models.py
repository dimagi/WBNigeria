import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from rapidsms import models as rapidsms

from aremind.apps.adherence.types import *
from aremind.apps.groups.models import Group
from aremind.apps.groups.utils import format_number

import logging
logger = logging.getLogger('patients.models')

class PatientDataPayload(models.Model):
    ''' Dumping area for incoming patient data XML snippets '''

    STATUS_CHOICES = (
        ('received', 'Received'),
        ('error', 'Error'),
        ('success', 'Success'),
    )

    raw_data = models.TextField()
    submit_date = models.DateTimeField()
    status = models.CharField(max_length=16, default='received',
                              choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)

    def save(self, **kwargs):
        if not self.pk:
            self.submit_date = datetime.datetime.now()
        return super(PatientDataPayload, self).save(**kwargs)

    def __unicode__(self):
        msg = u'Raw Data Payload, submitted on: {date}'
        return msg.format(date=self.submit_date)


class Patient(models.Model):
    # Patients may be manually created, so raw data can be null
    raw_data = models.ForeignKey(PatientDataPayload, null=True, blank=True,
                                 related_name='patients')
    contact = models.ForeignKey(rapidsms.Contact, unique=True)
    subject_number = models.CharField(max_length=20, unique=True)
    date_enrolled = models.DateField(default=datetime.date.today())
    mobile_number = models.CharField(max_length=30)
    pin = models.CharField(max_length=4, blank=True,
                           help_text="A 4-digit pin code for sms "
                                     "authentication workflows.")
    next_visit = models.DateField(blank=True, null=True)
    reminder_time = models.TimeField(blank=True, null=True)
    wisepill_msisdn = models.CharField(max_length=12, blank=True)
    # How many doses per day this patient is supposed to take
    daily_doses = models.IntegerField(default=0)

    def __unicode__(self):
        msg = u'Patient, Subject ID:{id}, Enrollment Date:{date_enrolled}'
        return msg.format(id=self.subject_number,
                          date_enrolled=self.date_enrolled)

    @property
    def formatted_phone(self):
        return format_number(self.mobile_number)

    def adherence(self):
        """Return adherence percent (integer, 0-100)
        based on Wisepill indication of doses taken in the
        last 7 days.
        This is simply the number of doses taken divided
        by the number supposed to have been taken over
        the period.

        Today doesn't count, since we can't know whether they've
        taken all the doses they're supposed to have taken by
        this time of day.

        Also looks to see what the oldest message we've ever
        received from this patient was. If it was less than 7
        days ago, assume they just got the device that long
        ago and only compute over that many days.

        If we've never received a message from them before today,
        report adherence = 0; as far as we know, they've never taken
        a dose (since today doesn't count).

        If their daily_doses is 0, report 100; their
        adherence is perfect.

        """
        today = datetime.date.today()
        beginning_of_today = datetime.datetime(today.year,
                                               today.month,
                                               today.day)

        # Messages we've gotten (today doesn't count)
        # pylint: disable-msg=E1101
        msgs = self.wisepill_messages.filter(timestamp__lt=beginning_of_today)

        # Are they supposed to take any?
        if self.daily_doses == 0:
            return 100 # perfect!

        # Have we ever gotten a message before today?
        if msgs.count() == 0:
            return 0  # never taken a dose...

        # When was our first message (ever)?
        first_message = msgs.order_by('timestamp')[0]
        days_to_first_message = (today - first_message.timestamp.date()).days
        if days_to_first_message < 7:
            days_to_count = days_to_first_message
        else:
            days_to_count = 7

        # compute adherence
        first_day_to_count = today - datetime.timedelta(days=days_to_count)
        num_wisepill_doses = msgs.filter(timestamp__gte=first_day_to_count). \
                                  count()
        supposed_to_take = days_to_count * self.daily_doses
        percent = int((100 * num_wisepill_doses) / supposed_to_take)
        if percent > 100:
            percent = 100  # 100 is the max
        return percent
        

class PatientPillsTaken(models.Model):
    """# of pills a patient took on a particular date"""
    patient = models.ForeignKey(Patient)
    date = models.DateField()
    num_pills = models.IntegerField(verbose_name="Number of Pills")

    def __unicode__(self):
        msg = u'Patient {id} took {num} pills on {date}'
        # pylint: disable-msg=E1101
        return msg.format(id=self.patient.subject_number,
                          date=self.date,
                          num=self.num_pills)

def remember_patient_pills_taken(patient,date,num_pills,origin):
    # FIXME: record the origin too (the source of the data)

    # get_or_create the pills taken record for this patient and date
    # so that if we get newer data for the same day, we just
    # overwrite the previous data
    taken,x = PatientPillsTaken.objects.get_or_create(patient=patient,
                                                      date=date,
                                                      defaults={'num_pills':num_pills})
    taken.num_pills = num_pills
    taken.save()

@receiver(post_save, sender=Patient)
def add_to_patient_group(sender, instance, created, **kwargs):
    if created:
        # add to subject group
        group_name = settings.DEFAULT_SUBJECT_GROUP_NAME
        group, _ = Group.objects.get_or_create(
            name=group_name, defaults={'is_editable': False}
        )
        instance.contact.groups.add(group)
    instance.contact.name = instance.subject_number
    instance.contact.save()
