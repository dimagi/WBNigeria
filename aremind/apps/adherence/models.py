import datetime
import hashlib
import locale
import logging
import time
import uuid

from django.db import models, transaction

from dateutil import rrule
import feedparser
from rapidsms import models as rapidsms
import twitter


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
        for contact in self.recipients.all():
            # Get feed entries to populate outgoing message
            feeds = contact.feeds.filter(active=True)
            try:
                entry = Entry.objects.filter(
                    feed__in=feeds,
                    published__lte=datetime.datetime.now()
                ).order_by('-published')[0]
                message = entry.content[:160]
            except IndexError:
                message = ""
            self.adherence_reminders.create(
                recipient=contact, date_queued=datetime.datetime.now(),
                date_to_send=self.date, message=message,
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


class FeedManager(models.Manager):

    def fetch_feeds(self):
        active_feeds = self.filter(active=True)
        total_entries = sum(map(lambda f: f.fetch_feed() or 0, active_feeds))
        return total_entries


class Feed(models.Model):
    TYPE_MANUAL = 'manual'
    TYPE_TWIITER = 'twitter'
    TYPE_RSS = 'rss'

    TYPE_CHOICES = (
        (TYPE_MANUAL, 'Manual Feed'),
        (TYPE_TWIITER, 'Twitter Feed'),
        (TYPE_RSS, 'RSS/Atom Feed'),
    )
 
    name = models.CharField(max_length=100,
        help_text=('Give a descriptive name for this feed. '
        'For Twitter feeds this should be the user screen name.')
    )
    feed_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MANUAL)
    url = models.URLField(blank=True, null=True, verify_exists=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    subscribers = models.ManyToManyField(rapidsms.Contact, related_name='feeds', blank=True)
    last_download = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)

    objects = FeedManager()

    def __unicode__(self):
        return u"{name} ({feed_type})".format(name=self.name, feed_type=self.get_feed_type_display())

    def fetch_feed(self):
        function_name = 'fetch_%s_feed' % self.feed_type
        fetch_function = getattr(self, function_name, None)
        if fetch_function:
            with transaction.commit_on_success():
                count = fetch_function()
            return count
        else:
            raise NotImplementedError('%s has not been implemented yet.' % function_name)
        
    def fetch_manual_feed(self):
        # Nothing to do here...
        pass

    def parse_twitter_date(self, string):
        locale.setlocale(locale.LC_TIME, 'C')
        date = datetime.datetime(*(time.strptime(string, '%a %b %d %H:%M:%S +0000 %Y')[0:6]))
        locale.setlocale(locale.LC_TIME, '')
        return date
         
    def fetch_twitter_feed(self):
        api = twitter.Api()
        try:
            timeline = api.GetUserTimeline(self.name)
        except TwitterError as e:
            logger.error(e)
            return None
        for status in timeline:
            if not self.description:
                self.description = status.user.description
            self.entries.get_or_create(
                uid=status.id,
                defaults={
                    'content': status.text,
                    'published': self.parse_twitter_date(status.created_at)
                }
            )
        self.last_download = datetime.datetime.now()
        self.save()
        return len(timeline)

    def fetch_rss_feed(self):
        data = feedparser.parse(self.url)
        if 'bozo' in data and data.bozo:
            logger.error('Bad Rss/Atom feed: %s' % self.url)
            return None
        for entry in data:
            if not self.description:
                self.description = data.feed.description or None
            pub_date = self._get_rss_pub_date(entry)    
            uid = self._get_rss_uid(entry)
            content = self._get_rss_content(entry)
            self.entries.get_or_create(
                uid=uid,
                defaults={
                    'content': content,
                    'published': pub_date
                }
            )
        self.last_download = datetime.datetime.now()
        self.save()
        return len(data)

    def _get_rss_pub_date(self, item):
        pub_date = None       
        for attr in ['updated_parsed','published_parsed', 'date_parsed', 'created_parsed']:
            if hasattr(item, attr):
                pub_date = getattr(item, attr)
                break
        if pub_date:
            try:
                ts = time.mktime(pub_date)
                pub_date = datetime.datetime.fromtimestamp(ts)
            except TypeError:
                pub_date = None
        return pub_date or datetime.datetime.now()

    def _get_rss_uid(self, item):
        link = item.link
        m = hashlib.md5()
        m.update(link)
        # Return the item id or the hashed link
        return item.get("id", m.hexdigest())

    def _get_rss_content(self, item):
        content = ''
        if hasattr(item, "summary"):
            content = item.content
        elif hasattr(item, "content"):
            content = item.content[0].value
        elif hasattr(item, "description"):
            content = item.description
        return content


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

