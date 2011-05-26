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

def make_tree():
    """Create a decisiontree Tree in the database.
    Returns the Tree object."""

    q1_text = _("How many pills did you miss in the last four days?")
    end_text = _("Thank you.")
    err_text = _("Sorry, please respond with a number. ")

    q1, x = Question.objects.get_or_create(text = q1_text,
                                           error_response = err_text + q1_text)
    state1,x = TreeState.objects.get_or_create(name = "state1",
                                             question = q1,
                                             num_retries = 3)

    answer,x = Answer.objects.get_or_create(name="numberofpills",
                                          type='R',
                                          answer=r"\d+")

    trans1,x = Transition.objects.get_or_create(current_state=state1,
                                              answer=answer,
                                              next_state=None) # end

    # We only use this internally, so not translated
    # Receipt of this message triggers starting the tree.
    trigger = "start tree"

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
    tree = make_tree()
    for patient in Patient.objects.all():
        start_tree_for_patient(tree, patient)

# When we complete an adherence survey, update adherence.pillsmissed
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
        return

    tree = session.tree
    entries = session.entries

    if entries.count() < 1:
        survey.completed(PatientSurvey.STATUS_NOT_COMPLETED)
        return

    entry = entries.all()[0]
    num_pills = int(entry.text)
    aremind.apps.adherence.models.PillsMissed(patient=patient,
                                              num_missed=num_pills,
                                              source=QUERY_TYPE_SMS).save()
    survey.completed(PatientSurvey.STATUS_COMPLETE)
