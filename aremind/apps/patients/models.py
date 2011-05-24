import datetime

from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from rapidsms import models as rapidsms

from aremind.apps.groups.models import Group
from aremind.apps.groups.utils import format_number
from decisiontree.app import session_end_signal

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

    def __unicode__(self):
        msg = u'Patient, Subject ID:{id}, Enrollment Date:{date_enrolled}'
        return msg.format(id=self.subject_number,
                          date_enrolled=self.date_enrolled)

    @property
    def formatted_phone(self):
        return format_number(self.mobile_number)

ADHERENCE_SOURCE_SMS = 0
ADHERENCE_SOURCE_IVR = 1
ADHERENCE_SOURCE_WISEPILL = 2
ADHERENCE_SOURCE = (
    (ADHERENCE_SOURCE_SMS, "SMS"),
    (ADHERENCE_SOURCE_IVR, "IVR"),
    (ADHERENCE_SOURCE_WISEPILL, "Wisepill"),
    )

class PatientPillsTaken(models.Model):
    """# of pills a patient took on a particular date"""
    patient = models.ForeignKey(Patient)
    date = models.DateField()
    num_pills = models.IntegerField(verbose_name="Number of Pills")

    def __unicode__(self):
        msg = u'Patient {id} took {num} pills on {date}'
        return msg.format(id=self.patient.subject_number,
                          date=self.date,
                          num=self.num_pills)


class PatientQueryResult(models.Model):
    """Whether an attempt to ask a patient about their
    adherence was completely successfully."""
    patient = models.ForeignKey(Patient)
    datetime = models.DateTimeField(auto_now_add=True)

    STATUS_COMPLETE = 0
    STATUS_NO_ANSWER = 1
    STATUS_NOT_COMPLETED = 2
    STATUS_ERROR = 3
    RESULT_STATUS = (
        (STATUS_COMPLETE, "Complete"),
        (STATUS_NO_ANSWER, "No answer"),
        (STATUS_NOT_COMPLETED, "Not completed"),
        (STATUS_ERROR, "Error"),
        )

    result_status = models.IntegerField(choices=RESULT_STATUS)
    adherence_source = models.IntegerField(choices=ADHERENCE_SOURCE)

    def __unicode__(self):
        msg = u'Patient {id} query by {adherence_source} on {datetime} result was {status}'
        # pylint: disable=E1101
        return msg.format(id=self.patient.subject_number,
                          datetime=self.datetime,
                          adherence_source=self.get_adherence_source_display(),
                          status=self.get_result_status_display())

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

def remember_query_result(patient, adherence_source, status):
    result = PatientQueryResult(patient=patient,
                                result_status=status,
                                adherence_source=adherence_source)
    result.save()

# When we complete an adherence survey, update patientpillstaken
@receiver(session_end_signal)
def session_end(sender, **kwargs):
    session = kwargs['session']
    canceled = kwargs['canceled']

    # find the patient
    connection = session.connection
    patient = Patient.objects.get(contact = connection.contact)

    if canceled:
        remember_query_result(patient,
                              ADHERENCE_SOURCE_SMS,
                              PatientQueryResult.STATUS_NOT_COMPLETED)
        return # don't save data

    tree = session.tree
    start_date = session.start_date
    entries = session.entries

    num_questions = 0
    for entry in entries.all():
        num_pills = int(entry.text)
        # the sequence # is the number of days ago we asked about
        date = start_date - datetime.timedelta(days=entry.sequence_id)
        remember_patient_pills_taken(patient, date, num_pills, "SMS")
        num_questions += 1
    if num_questions == 4:
        logger.debug('Got answers to 4 questions, recording complete')
        remember_query_result(patient,
                              ADHERENCE_SOURCE_SMS,
                              PatientQueryResult.STATUS_COMPLETE)
    else:
        logger.debug('Only got answers to %d questions, survey was not complete' % num_questions)
        remember_query_result(patient,
                              ADHERENCE_SOURCE_SMS,
                              PatientQueryResult.STATUS_NOT_COMPLETED)

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
