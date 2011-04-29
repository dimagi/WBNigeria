import datetime

from django.db import models

from rapidsms import models as rapidsms

from aremind.apps.groups.utils import format_number


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
    contact = models.ForeignKey(rapidsms.Contact, unique=True, related_name='patients')
    subject_number = models.CharField(max_length=20, unique=True)
    date_enrolled = models.DateField()
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

