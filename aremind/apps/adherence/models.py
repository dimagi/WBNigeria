import datetime
import hashlib
import locale
import logging
import random
import time
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils.html import strip_tags

from dateutil import rrule
import feedparser
from rapidsms import models as rapidsms
import twitter

from threadless_router.router import Router

import aremind.apps.adherence.sms
from aremind.apps.adherence.types import *
from aremind.apps.groups.models import Group
from aremind.apps.patients.models import Patient
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
        return u'{freq} at {time}'.format(freq=self.formatted_frequency, time=self.formatted_time)

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
            message = get_contact_message(contact)
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
        # pylint: disable-msg=E1101
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
        except twitter.TwitterError as e:
            logger.error(e)
            return None
        for status in timeline:
            if not self.description:
                self.description = status.user.description
            # pylint: disable-msg=E1101
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
        for entry in data.entries:
            if not self.description:
                self.description = data.feed.description or None
            pub_date = self._get_rss_pub_date(entry)    
            uid = self._get_rss_uid(entry)
            content = self._get_rss_content(entry)
            # pylint: disable-msg=E1101
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
            content = item.summary
        elif hasattr(item, "content"):
            content = item.content[0].value
        elif hasattr(item, "description"):
            content = item.description
        return self._clean_rss_content(content)

    def _clean_rss_content(self, content):
        return strip_tags(content)


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
    def seen_by(self, patient):
        EntrySeen.objects.get_or_create(entry=self, patient=patient)
        
class EntrySeen(models.Model):
    """Track that a particular patient has seen a particular entry"""
    entry = models.ForeignKey(Entry)
    patient = models.ForeignKey(Patient, related_name='entries_seen')

    class Meta(object):
        unique_together = ('entry','patient')

    def __unicode__(self):
        return u"Patient {name} has seen entry {feed}.{uid}".format(name=self.patient.subject_number, feed=self.entry.feed, uid=self.entry.uid)


def get_next_unseen_entry_for_patient(feeds, patient):
    try:
        entry = Entry.objects.filter(
            feed__in=feeds,
            published__lte=datetime.datetime.now()
        ).exclude(entryseen__patient=patient
        ).order_by('-published')[0]
        return entry
    except IndexError:
        return None

def forget_entries(feeds, patient):
    """Forget that the patient has seen any entries in these feeds"""
    EntrySeen.objects.filter(entry__feed__in=feeds,
                             patient=patient).delete()

def get_contact_message(contact):
    """Construct a message for the contact
    by grabbing the newest published entry from their feeds.
    Otherwise returns an empty string."""

    patient = Patient.objects.get(contact=contact)
    feeds = contact.feeds.filter(active=True)
    manual_feeds = feeds.filter(feed_type=Feed.TYPE_MANUAL)
    auto_feeds = feeds.exclude(feed_type=Feed.TYPE_MANUAL)

    logging.info("get message for %s.  %d manual feeds, %d auto feeds" % (patient,len(manual_feeds),len(auto_feeds)))

    manual_percent = getattr(settings, 'FEED_PERCENT_MANUAL', 25)
    prefer_manual = random.randrange(0,100) < manual_percent
    logging.info("manual percent = %d, prefer_manual=%s" % (manual_percent,prefer_manual))

    entry = None
    if prefer_manual:
        entry = get_next_unseen_entry_for_patient(manual_feeds, patient)
        if entry is None:
            # no unseen manual entries, forget they've seen them and try again
            forget_entries(manual_feeds, patient)
            entry = get_next_unseen_entry_for_patient(manual_feeds, patient)
        logging.info("got manual entry: %s" % entry)
    else:
        entry = get_next_unseen_entry_for_patient(auto_feeds, patient)
        logging.info("got auto entry: %s" % entry)
        
    if entry is None:
        # No luck so far, try any feed
        entry = get_next_unseen_entry_for_patient(feeds, patient)
        logging.info("got any entry: %s" % entry)

    if entry is None:
        # still no luck, forget they've seen anything and try again
        forget_entries(feeds, patient)
        entry = get_next_unseen_entry_for_patient(feeds, patient)
        logging.info("forgot all, got %s" % entry)

    if entry:
        entry.seen_by(patient)
        message = entry.content[:160]
    else:
        message = ""
    return message

class QuerySchedule(models.Model):
    """Schedule for starting queries to patients about adherence"""
    start_date = models.DateField()
    time_of_day = models.TimeField()
    recipients = models.ManyToManyField(Group,
                                        related_name='adherence_query_schedules')
    query_type = models.IntegerField(choices=ADHERENCE_SOURCE)
    last_run = models.DateTimeField(null=True, blank=True, editable=False)
    active = models.BooleanField(default=True)
    days_between = models.IntegerField()

    def __unicode__(self):
        msg = u"Schedule adherence queries starting on {start_date} "
        msg = msg + u"every {days_between} days "
        msg = msg + u"at {time_of_day} of type {query_type}"
        return msg.format(start_date=self.start_date,
                          time_of_day=self.time_of_day,
                          query_type=self.get_query_type_display(),
                          days_between=self.days_between)

    def should_run(self, force=False):
        """Return True if it's time to run this scheduled query."""
        if force:
            return True
        if not self.active:
            return False
        today = datetime.date.today()
        time_of_day = datetime.datetime.now().time()
        if time_of_day < self.time_of_day:
            # too early in the day for this one
            return False
        schedule_it = False
        if self.last_run is None:
            schedule_it = True
        else:
            days_since = today - self.last_run.date()
            if days_since >= datetime.timedelta(days=self.days_between):
                schedule_it = True
        return schedule_it

    def start_scheduled_queries(self, force=False):
        """Start any queries that are scheduled to start now."""
        if self.should_run(force):
            logger.debug("Starting query from schedule %s" % self)
            for group in self.recipients.all():
                for contact in group.contacts.all():
                    patient = Patient.objects.get(contact=contact)
                    survey = PatientSurvey(patient=patient,
                                           query_type=self.query_type)
                    survey.start()
            self.last_run = datetime.datetime.now()
            self.save()

class PatientSurveyException(Exception):
    pass
class SurveyAlreadyStartedException(PatientSurveyException):
    pass
class SurveyUnknownQueryTypeException(PatientSurveyException):
    pass

class PatientSurvey(models.Model):
    """One instance of asking a patient about their adherence, however
    we do it."""
    patient = models.ForeignKey(Patient, related_name='surveys')
    query_type = models.IntegerField(choices=QUERY_TYPES)
    last_modified = models.DateTimeField(auto_now=True)
    
    STATUS_CREATED = -2
    STATUS_STARTED = -1
    STATUS_COMPLETE = 0
    STATUS_NO_ANSWER = 1
    STATUS_NOT_COMPLETED = 2
    STATUS_ERROR = 3
    RESULT_STATUS = (
        (STATUS_CREATED, "Created"),
        (STATUS_STARTED, "Started"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_NO_ANSWER, "No answer"),
        (STATUS_NOT_COMPLETED, "Not completed"),
        (STATUS_ERROR, "Error"),
        )

    status = models.IntegerField(choices=RESULT_STATUS,
                                 default=STATUS_CREATED)

    def __unicode__(self):
        msg = u"PatientSurvey {id} for {patient} using {query_type} is {status}"
        return msg.format(id=self.pk,
                          patient=self.patient.subject_number,
                          query_type=self.get_query_type_display(),
                          status=self.get_status_display())

    @staticmethod
    def find_active(patient, query_type):
        """Find an active survey for this patient and query type.
        Return the survey object.  If multiple found, return one
        of them. If not found, return None."""
        surveys = PatientSurvey.objects.filter(patient=patient,
                                               query_type=query_type,
                                               status=PatientSurvey.STATUS_STARTED)
        if len(surveys) == 0:
            return None
        return surveys[0]

    def start(self):
        logger.debug("PatientSurvey.start")
        if self.status != self.STATUS_CREATED:
            raise SurveyAlreadyStartedException()

        if self.query_type == QUERY_TYPE_SMS:
            tree = aremind.apps.adherence.sms.make_tree()
            aremind.apps.adherence.sms.start_tree_for_patient(tree, self.patient)
        elif self.query_type == QUERY_TYPE_IVR:
            url = reverse('patient-ivr-callback',
                          kwargs={'patient_id': self.patient.pk})
            backend = Router().backends['tropo']
            backend.call_tropo(url, message_type='voice')
            # tropo will POST to our callback which will continue things
        else:
            raise SurveyUnknownQueryTypeException()

        self.status = self.STATUS_STARTED
        self.save()

    def completed(self, status):
        self.status = status
        logger.debug("PatientSurvey completed: %s" % self)
        self.save()

class PillsMissed(models.Model):
    """Pills patient says they missed in the four days before
    a given date"""
    patient = models.ForeignKey(Patient)
    date = models.DateTimeField(auto_now=True)
    num_missed = models.IntegerField()
    source = models.IntegerField(choices=QUERY_TYPES)

    class Meta:
        verbose_name_plural = "Pills missed"

    def __unicode__(self):
        msg = u"Patient {patient} missed {num_missed} pills "
        msg = msg + u"in the four days before {date} "
        msg = msg + u"according to {source}."
        return msg.format(patient=self.patient,
                          num_missed=self.num_missed,
                          date=self.date,
                          source=self.get_source_display())
