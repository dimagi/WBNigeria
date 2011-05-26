# Code related to using decisiontree to survey using SMS

import datetime
import logging

from django.dispatch import receiver
from decisiontree.app import session_end_signal
from decisiontree.models import Question, Answer, Tree, TreeState, Transition
from threadless_router.base import incoming
import aremind.apps.adherence.models
from aremind.apps.adherence.types import *
from aremind.apps.patients.models import Patient, remember_patient_pills_taken

logger = logging.getLogger('adherence.sms')

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s

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

# When we complete an adherence survey, update patientpillstaken
@receiver(session_end_signal)
def session_end(sender, **kwargs):
    session = kwargs['session']
    canceled = kwargs['canceled']

    # for convenience
    PatientSurvey = aremind.apps.adherence.models.PatientSurvey

    # find the patient
    connection = session.connection
    patient = Patient.objects.get(contact = connection.contact)
    survey = PatientSurvey.find_active(patient, QUERY_TYPE_SMS)

    if canceled:
        survey.completed(PatientSurvey.STATUS_NOT_COMPLETED)
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
        survey.completed(PatientSurvey.STATUS_COMPLETE)
    else:
        logger.debug('Only got answers to %d questions, survey was not complete' % num_questions)
        survey.completed(PatientSurvey.STATUS_NOT_COMPLETED)

