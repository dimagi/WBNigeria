import datetime
import logging
import uuid

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

    WEEKDAY_CHOICES = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    frequency = models.CharField(max_length=16, choices=REPEAT_CHOICES,
        default=REPEAT_DAILY, db_index=True
    )
    weekdays = models.CommaSeparatedIntegerField(max_length=20, blank=True, null=True)
    time_of_day = models.TimeField()
    recipients = models.ManyToManyField(rapidsms.Contact, related_name='reminders', blank=True)

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

    @property
    def formatted_frequency(self):
        display = self.get_frequency_display()
        if self.frequency == self.__class__.REPEAT_WEEKLY:
            names = map(lambda x: self.__class__.WEEKDAY_CHOICES[x][1], map(int, self.weekdays.split(',')))
            display = u'%s (%s)' % (display, u', '.join(names))
        return display

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
            # Get feed entries to populate outgoing message
            feeds = contact.feeds.filter(active=True)
            try:
                entry = Entry.objects.filter(
                    published__lte=datetime.datetime.now()
                ).order_by('-published')[0]
                message = entry.content[:160]
            except IndexError:
                message = ""
            self.adherence_reminders.create(
                recipient=contact, date_queued=datetime.datetime.now(),
                message=message,
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
            reminder=self.reminder, recipient=self.recipient,
            date=self.date_queued
        )


class Feed(models.Model):
    TYPE_MANUAL = 'manual'
    TYPE_TWIITER = 'twitter'
    TYPE_RSS = 'rss'
    TYPE_ATOM = 'atom'

    TYPE_CHOICES = (
        (TYPE_MANUAL, 'Manual Feed'),
        (TYPE_TWIITER, 'Twitter Feed'),
        (TYPE_RSS, 'RSS Feed'),
        (TYPE_RSS, 'Atom Feed'),
    )
 
    name = models.CharField(max_length=100)
    feed_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MANUAL)
    url = models.URLField(blank=True, null=True, verify_exists=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    subscribers = models.ManyToManyField(rapidsms.Contact, related_name='feeds', blank=True)
    last_download = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u"{name} ({feed_type})".format(name=self.name, feed_type=self.get_feed_type_display())


def default_uid():
    return uuid.uuid4().hex


class Entry(models.Model):
    feed = models.ForeignKey(Feed, related_name='entries')
    uid = models.CharField(max_length=255, default=default_uid)
    content = models.TextField()
    published = models.DateTimeField(default=datetime.datetime.now)
    added = models.DateTimeField(auto_now_add=True, default=datetime.datetime.now)

    class Meta(object):
        unique_together = ('feed', 'uid', )
        ordering = ('-published', )

    def __unicode__(self):
        return u"Entry {name} for ({feed})".format(name=self.uid, feed=self.feed)

