import datetime
import logging

from django.db import models

from dateutil import rrule
from rapidsms import models as rapidsms


logger = logging.getLogger('adherence.models')


class ReminderReadyManager(models.Manager):
    def ready(self):
        qs = super(ReminderReadyManager, self).get_query_set()
        qs = qs.filter(date__lt=datetime.datetime.now())
        return qs


class Reminder(models.Model):
    REPEAT_DAILY = 'daily'
    REPEAT_WEEKLY = 'weekly'

    REPEAT_CHOICES = (
        (REPEAT_DAILY, 'Daily'),
        (REPEAT_WEEKLY, 'Weekly'),
    )
    frequency = models.CharField(max_length=16, choices=REPEAT_CHOICES,
        default=REPEAT_DAILY, db_index=True
    )
    weekdays = models.CommaSeparatedIntegerField(max_length=20, blank=True, null=True)
    time_of_day = models.TimeField()
    recipients = models.ManyToManyField(rapidsms.Contact, related_name='reminders')

    date_last_notified = models.DateTimeField(null=True, blank=True)
    date = models.DateTimeField(db_index=True)

    objects = ReminderReadyManager()

    def __unicode__(self):
        return u'{freq} reminder at {time}'.format(freq=self.frequency, time=self.formatted_time)

    def save(self, *args, **kwargs):
        today = datetime.date.today()
        if not self.date:
            self.date = datetime.datetime.combine(today, self.time_of_day)
        super(Reminder, self).save(*args, **kwargs)

    @property
    def formatted_time(self):
        return self.time_of_day.strftime('%I:%M %p')

    def get_next_date(self):
        """ calculate next date based on configured characteristics """
        logger.debug('get_next_date - {0}'.format(self))
        now = datetime.datetime.now()
        # return current date if it's in the future
        if self.date > now:
            return self.date
        freq_map = {
            self.__class__.REPEAT_DAILY: rrule.DAILY,
            self.__class__.REPEAT_WEEKLY: rrule.WEEKLY,
        }
        freq = freq_map.get(self.frequency)
        start = datetime.datetime.combine(self.date.date(), self.time_of_day)
        kwargs = {'dtstart': start}
        if freq == rrule.WEEKLY:
            try:
                weekdays = map(int, self.weekdays.split(','))
            except TypeError:
                weekdays = None
                logger.debug('Invalid weekday data: {reminder} ({pk})'.format(reminder=self, pk=self.pk))
            if weekdays:
                kwargs['byweekday'] = weekdays
        dates = rrule.rrule(freq, **kwargs)
        for date in dates:
            logger.debug('looking for next date {0}'.format(date))
            if date > now:
                logger.debug('next date {0}'.format(date))
                return date

    def set_next_date(self):
        """ update broadcast to be ready for next date """
        logger.debug('set_next_date start - {0}'.format(self))
        now = datetime.datetime.now()
        next_date = self.get_next_date()
        self.date_last_notified = now
        if next_date:
            self.date = next_date
        logger.debug('set_next_date end - {0}'.format(self))
        self.save()

    def queue_outgoing_messages(self):
        """ generate queued outgoing messages """

        for contact in self.recipients:
            self.adherence_reminders.create(
                recipient=contact, date_queued=datetime.datetime.now()
            )
        return self.recipients.count()


class SendReminder(models.Model):
    STATUS_QUEUED = 'queued'
    STATUS_SENT = 'sent'
    STATUS_ERROR = 'error'

    STATUS_CHOICES = (
        (STATUS_QUEUED, 'Queued'),
        (STATUS_SENT, 'Sent'),
        (STATUS_ERROR, 'Error'),
    )

    reminder = models.ForeignKey(Reminder, related_name='adherence_reminders')
    recipient = models.ForeignKey(rapidsms.Contact,
        related_name='adherence_reminders',
        help_text='The recipient of this notification.'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    date_queued = models.DateTimeField(help_text='The date and time this '
                                       'reminder was initially created.')
    date_to_send = models.DateTimeField(help_text='The date and time this reminder'
                                        ' is scheduled to be sent.')
    date_sent = models.DateTimeField(null=True, blank=True,
        help_text='The date and time this reminder was sent.')
    message = models.CharField(max_length=160, null=True, blank=True, 
        help_text='The actual message that was sent to the user.'
    )
    
    def __unicode__(self):
        return u'{reminder} for {recipient} created on {date}'.format(
                                        reminder=self.reminder,
                                        recipient=self.recipient,
                                        date=self.date_queued)

    def get_message(self):
        # TODO: Retrive messages from the various streams
        if not self.message:
            self.message = u'Time to take your pills'
        return self.message

