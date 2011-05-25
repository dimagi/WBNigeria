import datetime
import logging
import random

from django import http
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from rapidsms.messages.incoming import IncomingMessage
from threadless_router.router import Router

from apps.patients.models import Patient

logger = logging.getLogger('wisepill.views')

#  url(r'^list_messages/(?p<patient_id>\d+)/$', 'list_messages_for_patient', name='wisepill-list-messages-for-patient'),

@login_required
def list_messages_for_patient(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    context = { 'patient': patient,
                'wisepill_messages': patient.wisepill_messages.all() }
    return render(request, 'wisepill/list_messages_for_patient.html', context)

@login_required
def index(request):
    return http.HttpResponse('')

@login_required
def make_fake_message(request, patient_id):
    """Make up a message for the patient's wisepill device
    and fake it coming in"""
    logger.debug('make_fake_message')
    patient = get_object_or_404(Patient, pk=patient_id)
    msisdn = patient.wisepill_msisdn
    timestamp = datetime.datetime.now()
    # 50-50 whether to make a delayed message
    is_delayed = random.randint(0,99) > 50
    if is_delayed:
        timestamp -= datetime.timedelta(minutes=10)
    
    delay_value = "03" if is_delayed else "02"
    # DDMMYYHHMMSS
    time_value = timestamp.strftime("%d%m%y%H%M%S")

    text = "@={delay_value},CN={msisdn},SN=fake,T={time_value},S=20,B=3800,PC=1,U=fake,M=1,CE=0".format(**locals())

    connection = patient.contact.default_connection

    msg = IncomingMessage(connection=connection,
                          text=text)
    router = Router()
    router.incoming(msg)    
    return redirect('patient-list')
