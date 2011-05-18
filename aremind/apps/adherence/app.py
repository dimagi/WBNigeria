#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import datetime

from rapidsms.apps.base import AppBase
from rapidsms.messages import OutgoingMessage

from aremind.apps.adherence.models import Reminder, SendReminder


# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s


class AdherenceApp(AppBase):

    reminder = _('ARemind:')

    def start(self):
		self.info('started')

    def queue_outgoing_messages(self):
        """ generate queued messages for adherence reminders """
        reminders = Reminder.objects.ready()
        self.info('found {0} ready adherence reminder(s)'.format(reminders.count()))
        for reminder in reminders:
            # TODO: make sure this process is atomic
            count = reminder.queue_outgoing_messages()
            self.debug('queued {0} adherence reminder(s)'.format(count))
            reminder.set_next_date()

    def send_messages(self):
        """ send queued for delivery messages """

        messages = SendReminder.objects.filter(status='queued')[:50]
        self.info('found {0} reminder(s) to send'.format(messages.count()))
        for message in messages:
            connection = message.recipient.default_connection
            template = u'{reminder} {content}'.format(
                reminder=self.reminder,
                content=message.message or ""
            )
            if len(template) > 160:
                # Truncate at 160 characters but keeping whole words
                template = template[:160]
                words = template.split(' ')[:-1]
                template = u' '.join(words) + u'...'
            msg = OutgoingMessage(connection=connection, template=template)
            success = True
            try:
                self.router.outgoing(msg)
            except Exception, e:
                self.exception(e)
                success = False
            if success and msg.sent:
                self.debug('message sent successfully')
                message.status = 'sent'
                message.date_sent = datetime.datetime.now()
            else:
                self.debug('message failed to send')
                message.status = 'error'
            message.save()

    def cronjob(self):
        self.debug('cron job running')
        # grab all broadcasts ready to go out and queue their messages
        self.queue_outgoing_messages()
        # send queued messages
        self.send_messages()

