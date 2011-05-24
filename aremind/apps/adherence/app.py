#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import datetime
import logging

from rapidsms.apps.base import AppBase
from rapidsms.messages import OutgoingMessage

from aremind.apps.adherence.models import Reminder, SendReminder, QuerySchedule
from aremind.apps.patients.models import Patient
from decisiontree.models import Question, Answer, Tree, TreeState, Transition

from threadless_router.base import incoming

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
        # Start any adherence queries
        for query_schedule in QuerySchedule.objects.filter(active=True):
            query_schedule.start_scheduled_queries()

def make_tree_for_day(date):
    """Create a decisiontree Tree in the database for the given date.
    Returns the Tree object.
    Date should be a python datetime.date."""

    # Names for weekdays that we need
    yesterday = (date - datetime.timedelta(days=1)).strftime("%A")
    daybeforeyesterday = (date - datetime.timedelta(days=2)).strftime("%A")
    daybeforedaybeforeyesterday = (date - datetime.timedelta(days=3)).strftime("%A")
    daybeforedaybeforedaybeforeyesterday = (date - datetime.timedelta(days=4)).strftime("%A")

    q1_text = _("Yesterday was %(yesterday)s. How many pills did you take from the grey study pillbox yesterday?") % locals()
    q2_text = _("The day before yesterday was %(daybeforeyesterday)s. Tell me how many pills you took from the grey study pillbox on %(daybeforeyesterday)s.") % locals()
    q3_text = _("How about the day before that? Tell me how many pills you took from the grey study pillbox on %(daybeforedaybeforeyesterday)s.") % locals()
    q4_text = _("4 days ago was %(daybeforedaybeforedaybeforeyesterday)s. Tell me how many pills you took from the grey study pillbox on %(daybeforedaybeforedaybeforeyesterday)s. Please key in the number on your phone's touchpad.") % locals()
    q4_err = _("Sorry, please key in the number of pills you took from the grey study pillbox on %(daybeforedaybeforedaybeforeyesterday)s.") % locals()
    end_text = _("Thank you.")
    err_text = _("Sorry, please respond with a number. ")

    # For most questions, on error just put err_text in front and send again.
    # But Q4 gets too long for an SMS if we do that, so we need to compose
    # a custom shorter message there.

    q1,x = Question.objects.get_or_create(text = q1_text,
                                          error_response = err_text + q1_text)
    q2,x = Question.objects.get_or_create(text = q2_text,
                                          error_response = err_text + q2_text)
    q3,x = Question.objects.get_or_create(text = q3_text,
                                          error_response = err_text + q3_text)
    q4,x = Question.objects.get_or_create(text = q4_text,
                                          error_response = q4_err)

    state1,x = TreeState.objects.get_or_create(name = "state1",
                                             question = q1,
                                             num_retries = 3)
    state2,x = TreeState.objects.get_or_create(name = "state2",
                                             question = q2,
                                             num_retries = 3)
    state3,x = TreeState.objects.get_or_create(name = "state3",
                                             question = q3,
                                             num_retries = 3)
    state4,x = TreeState.objects.get_or_create(name = "state4",
                                             question = q4,
                                             num_retries = 3)

    answer,x = Answer.objects.get_or_create(name="numberofpills",
                                          type='R',
                                          answer=r"\d+")

    trans1,x = Transition.objects.get_or_create(current_state=state1,
                                              answer=answer,
                                              next_state=state2)
    trans2,x = Transition.objects.get_or_create(current_state=state2,
                                              answer=answer,
                                              next_state=state3)
    trans3,x = Transition.objects.get_or_create(current_state=state3,
                                              answer=answer,
                                              next_state=state4)
    trans4,x = Transition.objects.get_or_create(current_state=state4,
                                                answer=answer,
                                                next_state=None) # end

    # We only use this internally, so not translated
    # Receipt of this message triggers starting the tree.
    trigger = "start tree on %s" % date.strftime("%A")

    tree,x = Tree.objects.get_or_create(trigger = trigger.lower(),
                                        root_state = state1,
                                        completion_text = end_text)

    return tree

def start_tree_for_patient(tree, patient):
    """Trigger tree for a given patient.
    Will result in our sending them the first question in the tree."""

    # fake an incoming message from our patient that triggers the tree

    connection = patient.contact.default_connection
    backend_name = connection.backend.name
    address = connection.identity
    incoming(backend_name, address, tree.trigger)

def start_tree_for_all_patients():
    logging.debug("start_tree_for_all_patients")
    tree = make_tree_for_day(datetime.date.today())
    for patient in Patient.objects.all():
        start_tree_for_patient(tree, patient)
