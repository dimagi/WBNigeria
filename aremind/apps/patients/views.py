import datetime
import logging

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from aremind.decorators import has_perm_or_basicauth
from aremind.apps.adherence.models import Entry
from aremind.apps.patients import models as patients
from aremind.apps.patients.forms import PatientRemindersForm, PatientOnetimeMessageForm
from aremind.apps.patients.importer import parse_payload


logger = logging.getLogger('aremind.apps.patients')


@csrf_exempt
@require_http_methods(['POST'])
@has_perm_or_basicauth('patients.add_patientdatapayload', 'Patients')
def receive_patient_record(request):
    ''' Accept data submissions from the the site via POST. '''
    if request.META['CONTENT_TYPE'] != 'text/xml':
        logger.warn('incoming post does not have text/xml content type')
        logger.debug(request)
    content = request.raw_post_data
    if not content:
        logger.error("No XML data appears to be attached.")
        return http.HttpResponseServerError("No XML data appears to be attached.")
    payload = patients.PatientDataPayload.objects.create(raw_data=content)
    try:
        parse_payload(payload)
    except Exception as e:
        mail_admins(subject="Patient Import Failed", message=unicode(e))
        return http.HttpResponseServerError(unicode(e))
    return http.HttpResponse("Data submitted succesfully.")


@login_required
def list_patients(request):
    patients_list = patients.Patient.objects.all().annotate(
        reminder_count=Count('contact__reminders', distinct=True),
        feed_count=Count('contact__feeds', distinct=True)
    )
    context = {'patients': patients_list}
    return render(request, 'patients/patient_list.html', context)



@login_required
def view_patient(request, patient_id):
    patient = get_object_or_404(patients.Patient, pk=patient_id)
    if request.method == 'POST':
        form = PatientRemindersForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.info(request, "Patient info saved.")
            return redirect('patient-list')
    else:
        form = PatientRemindersForm(instance=patient)
    context = {'patient': patient, 'form': form}
    return render(request, 'patients/patient_detail.html', context)

# FIXME: refactor this so test_messager and we use common code
def _get_backend():
    from django.conf import settings
    from rapidsms.models import Backend
    from threadless_router.router import Router
    
    if hasattr(settings, 'TEST_MESSAGER_BACKEND'):
        backend_name = settings.TEST_MESSAGER_BACKEND
        try:
            backend = Backend.objects.get(name=backend_name)
        except Backend.DoesNotExist:
            backend = None
        if backend:
            return backend
    # pick one at 'random' - whichever one's key is first returned by keys()
    # FIXME: handle case of no backends
    router = Router()
    backend_name = router.backends.keys()[0]
    backend = Backend.objects.get(name=backend_name)
    return backend

@login_required
def patient_onetime_message(request, patient_id):
    from rapidsms.models import Connection
    from rapidsms.messages import OutgoingMessage
    from threadless_router.router import Router

    patient = get_object_or_404(patients.Patient, pk=patient_id)
    if request.method == 'POST':
        form = PatientOnetimeMessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            number = patient.mobile_number
            backend = _get_backend()

            connection, _ = Connection.objects.get_or_create(backend=backend,
                                                             identity=number)
            msg = OutgoingMessage(connection, message)
            router = Router()
            if router.backends[backend.name].send(msg):
                messages.success(request, "Message sent to patient %s" % patient.subject_number)
            else:
                messages.error(request, "An error occurred while trying to send the message to patient %s" % patient.subject_number)

            return redirect('patient-list')
    else:
        # FIXME - this code copied from apps/adherence/models.py Reminder.queue_outgoing_messages
        # Set default message
        feeds = patient.contact.feeds.filter(active=True)
        try:
            entry = Entry.objects.filter(
                feed__in=feeds,
                published__lte=datetime.datetime.now()
            ).order_by('-published')[0]
            message = entry.content[:160]
        except IndexError:
            message = ""
        form = PatientOnetimeMessageForm(initial={'message': message})
    context = { 'patient': patient, 'form': form }
    return render(request, 'patients/patient_onetime_message.html', context)
