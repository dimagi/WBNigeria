import datetime
import json
import logging

from django import http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from rapidsms.messages import OutgoingMessage
from rapidsms.models import Connection
import rapidsms.contrib.messagelog.models as messagelog
from threadless_router.router import Router

from aremind.decorators import has_perm_or_basicauth
from aremind.apps.adherence.models import (get_contact_message, PatientSurvey,
                                           PillsMissed)
from aremind.apps.adherence.types import *
from aremind.apps.patients import models as patients
from aremind.apps.patients.models import Patient
from aremind.apps.patients.forms import PatientRemindersForm, PatientOnetimeMessageForm, PillHistoryForm
from aremind.apps.patients.importer import parse_payload
from aremind.apps.reminders.forms import ReportForm, MonthReportForm

from dimagi.utils.dates import get_day_of_month


logger = logging.getLogger('aremind.apps.patients')
logger.setLevel(logging.DEBUG)

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


#@login_required
#def list_patients(request):
#    patients_list = patients.Patient.objects.all().annotate(
#        reminder_count=Count('contact__reminders', distinct=True),
#        feed_count=Count('contact__feeds', distinct=True),
#        message_count=Count('wisepill_messages', distinct=True),
#    )
#    context = {'patients': patients_list}
#    return render(request, 'patients/patient_list.html', context)


def get_patient_stats_context(appt_date):
    context = {}
    patients_list = patients.Patient.objects.annotate(
        reminder_count=Count('contact__reminders', distinct=True),
        feed_count=Count('contact__feeds', distinct=True),
        message_count=Count('wisepill_messages', distinct=True),
    )
    for patient in patients_list:
        wpmessages = patient.wisepill_messages.all()
        wpsparkline = []
        for day in range(20):
            dateStart =  appt_date - datetime.timedelta(days=day)
            msgs = wpmessages.filter(timestamp__year=dateStart.year, timestamp__month=dateStart.month, timestamp__day=dateStart.day)
            msgCount = msgs.count()
            wpsparkline.insert(0,msgCount)
        patient.wisepill_sparkline = wpsparkline

        pmSparkline = []
        dateStartWeek = appt_date
        dateEndWeek = appt_date - datetime.timedelta(days=7)
        for week in range(8):
            pillsMissed = patient.pillsmissed_set.filter(date__lt=dateStartWeek, date__gt=dateEndWeek, source=1) #we should only find at most 1 per week...
            if(len(pillsMissed) > 0):
                pmSparkline.insert(0,(-1)*pillsMissed[0].num_missed)
            else:
                pmSparkline.insert(0,0)
            dateStartWeek = dateEndWeek
            dateEndWeek = dateEndWeek - datetime.timedelta(days=7)


        patient.report_adherence = patient.adherence_report_date(appt_date)

        patient.pills_missed_parkline = pmSparkline


    context['patients'] = patients_list;
    return context

@login_required
def list_patients(request):
    today = datetime.date.today()
    appt_date = today + datetime.timedelta(weeks=1)
    form = ReportForm(request.GET or None)
    if form.is_valid():
        appt_date = form.cleaned_data['date'] or appt_date
    context = get_patient_stats_context(appt_date)
    context['report_form'] =  form
    return render(request, 'patients/patient_stats.html', context)


def get_patient_stats_detail_context(report_date, patient_id):
    context = {}
    if not patient_id:
        patients = Patient.objects.all()
    else:
        patients = Patient.objects.filter(id=patient_id)
        if(len(patients) > 0):
            context["daily_doses"] = patients[0].daily_doses

    context["patients"] = patients
    if not report_date:
        report_date = datetime.now()

    days = get_day_of_month(report_date.year,report_date.month,-1).day
    wp_usage_rows = []
    for day in range(1,days+1):
        row_date = datetime.date(report_date.year,report_date.month, day)
        row = []
        row.append(row_date)
        for patient in patients:
            msg_count = patient.wisepill_messages.filter(timestamp__year=row_date.year,timestamp__month=row_date.month,timestamp__day=row_date.day).count()
            row.append(msg_count)
        wp_usage_rows.append(row)

    pill_count_data = {}
    for patient in patients:
        pill_count_data["patient_id"] = patient.subject_number
        pills_missed_data = []
        num_days_in_report_month = days
        num_weeks_in_report_month = num_days_in_report_month / 7
        for week in range(0,num_weeks_in_report_month + 1):
            week_start = (datetime.date(report_date.year,report_date.month,1) + datetime.timedelta(days=week*7))
            week_end = week_start + datetime.timedelta(days=7)
            pm_week_data = {}

            pills_missed_set = patient.pillsmissed_set.filter(date__gt=week_start, date__lt=week_end, source=1) # source = 1 means SMS
            if(len(pills_missed_set) > 0):
                pills_missed_week = pills_missed_set.aggregate(Count('num_missed'))["num_missed__count"]
            else:
                pills_missed_week = "No Response"
            pm_week_data["pills_missed"] = pills_missed_week
            pm_week_data["week_start"] = week_start
            pm_week_data["week_end"] = week_end
            pills_missed_data.append(pm_week_data)
        pill_count_data["pill_count_data"] = pills_missed_data
    context["wp_usage_rows"] = wp_usage_rows
    context["pm_data"] = pill_count_data
    context["pm_weeks"] = pill_count_data["pill_count_data"]
    return context

@login_required
def list_patient_stats_detail(request, patient_id=None):
    today = datetime.date.today()
    report_date = today + datetime.timedelta(weeks=1)
    form = MonthReportForm(request.GET or None)
    if form.is_valid():
        report_date = form.cleaned_data['date'] or report_date
    context = get_patient_stats_detail_context(report_date, patient_id)
    context['report_form'] =  form
    context['report_date'] = report_date
    context['report_month'] = report_date.strftime('%B')
    return render(request, 'patients/patient_stats_detail.html', context)


@login_required
def create_edit_patient(request, patient_id=None):
    if patient_id:
        patient = get_object_or_404(patients.Patient, pk=patient_id)
    else:
        patient = patients.Patient()
    if request.method == 'POST':
        form = PatientRemindersForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.info(request, "Patient info saved.")
            return redirect('patient-list')
    else:
        form = PatientRemindersForm(instance=patient)
    context = {'patient': patient, 'form': form}
    return render(request, 'patients/create_edit_patient.html', context)

@login_required
def messages_to_patient(request, patient_id):
    patient = get_object_or_404(patients.Patient, pk=patient_id)
    contact = patient.contact
    connections = Connection.objects.filter(contact=contact)
    messages = messagelog.Message.objects.filter(
        Q(contact=patient.contact) | Q(connection__in=connections),
        direction="O") \
        .order_by('-date')
    # note - can't call these 'messages' in the request context because
    # then our base template will try to render them as Django 'messages'
    context = dict(patient=patient, texts=messages)
    return render(request, 'patients/messages_to_patient.html', context)


@login_required
def patient_onetime_message(request, patient_id):
    """Send a onetime message to a patient.
    Default to getting it from their feeds but allow editing that."""

    patient = get_object_or_404(patients.Patient, pk=patient_id)
    if request.method == 'POST':
        form = PatientOnetimeMessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            connection = patient.contact.default_connection
            msg = OutgoingMessage(connection, message)
            router = Router()
            success = True
            try:
                router.outgoing(msg)
            except Exception, e:
                logger.exception(e)
                success = False
            if success:
                messages.success(request, "Message sent to patient %s" % patient.subject_number)
            else:
                messages.error(request, "An error occurred while trying to send the message to patient %s" % patient.subject_number)

            return redirect('patient-list')
    else:
        # Set default message
        message = get_contact_message(patient.contact)
        form = PatientOnetimeMessageForm(initial={'message': message})
    context = { 'patient': patient, 'form': form }
    return render(request, 'patients/patient_onetime_message.html', context)

@login_required
def patient_start_adherence_tree(request, patient_id):
    """Start adherence tree interaction with patient."""
    patient = get_object_or_404(patients.Patient, pk=patient_id)
    survey = PatientSurvey(patient=patient, query_type=QUERY_TYPE_SMS, is_test=True)
    survey.start()
    return redirect('patient-list')

@login_required
def patient_start_ivr(request, patient_id):
    """Start interactive voice interaction with patient."""
    patient = get_object_or_404(patients.Patient, pk=patient_id)
    survey = PatientSurvey(patient=patient, query_type=QUERY_TYPE_IVR, is_test=True)
    survey.start()
    return redirect('patient-list')

@csrf_exempt
def patient_ivr_complete(request, patient_id):
    """
    We tell tropo to call us back at this view's URL with the results
    (good or bad) of running an IVR.
    """

    logger.debug("##%s" % request.raw_post_data)

    patient = get_object_or_404(patients.Patient, pk=patient_id)
    survey = PatientSurvey.find_active(patient, QUERY_TYPE_IVR)

        

    try:
        if not survey:
            logger.error("Could not find an IVR survey in progress for patient %s" % patient)
            return http.HttpResponseServerError()

        postdata = json.loads(request.raw_post_data)
        
        if 'result' in postdata:
            # Survey result
            result = postdata['result']
            logger.debug("## Results=%r" % result)
            if 'error' in result and result['error'] is not None:
                logger.error("## Error from phone survey: %s" % result['error'])
                survey.completed(PatientSurvey.STATUS_ERROR)
                return http.HttpResponse()

            if result['complete'] == False:
                survey.completed(PatientSurvey.STATUS_NO_ANSWER)
                return http.HttpResponse()
                                      
            if 'actions' not in result:
                # Some kind of error
                if result['state'] == 'DISCONNECTED':
                    # seem to get this if we hang up in the middle
                    survey.completed(PatientSurvey.STATUS_NOT_COMPLETED)
                    return http.HttpResponse()

            actions = result['actions']
            # actions can be either an array of dictionaries or a single
            # dictionary, sigh.  Figure out if it's a single dictionary
            # and wrap it in an array to avoid insanity.
            if isinstance(actions, dict):
                actions = [actions, ]
            num_questions_answered = 0
            complete = False
            error = False
            for item in actions:
                logger.debug("## action=%s", item)
                if item['name'] == 'question1' and \
                       item['disposition'] == 'SUCCESS':
                        # Got an answer, yay
                        answer = item['value']
                        num_pills = int(answer)
                        if not survey.is_test:
                            # remember result
                            PillsMissed(patient=patient,
                                        num_missed=num_pills,
                                        source=QUERY_TYPE_IVR).save()
                        complete = True
                elif item['disposition'] == 'TIMEOUT':
                    pass #incomplete = True
                else:
                    logger.debug("## Error on question %s for patient: disposition %s" % (item['name'], item['disposition']))
                    error = True
            if error:
                status = PatientSurvey.STATUS_ERROR
            elif not complete:
                status = PatientSurvey.STATUS_NOT_COMPLETED
            else:
                status = PatientSurvey.STATUS_COMPLETE
            survey.completed(status)
            return http.HttpResponse()
        # whoops
        logger.error("patient_ivr_complete called with no result data!!")
        survey.completed(PatientSurvey.STATUS_ERROR)
        return http.HttpResponseServerError()
    except Exception,e:
        logger.exception(e)
        survey.completed(PatientSurvey.STATUS_ERROR)
        return http.HttpResponseServerError()

def audio_file_url(filename):
    """Given a filename, work out the URL that tropo needs to use
    to download it from us.  Tropo apparently needs the full URL,
    at least otherwise it reads out the filename instead of
    downloading and playing it :-(
    We're going to end up with something like
    http://example.com:8000/static/audio/01-Intro.mp3
    """
    root = settings.STATIC_URL  # ends in '/'
    use_ssl = getattr(settings, 'USE_SSL_FOR_AUDIO_FILE_URLS', False)
    alt_domain = getattr(settings, 'IVR_AUDIO_DOMAIN_URL', False) #an unfortunate tropo necessary hack.
    scheme = "https" if use_ssl else "http"
    url = "%s://%s%saudio/%s" % (scheme, Site.objects.get_current().domain, root, filename)
    if(alt_domain):
        url = "http://%s%saudio/%s" % (alt_domain, root, filename)
    logging.info("##AUDIO_URL=%s" % url)
    return url

# Maybe this should be a setting
USE_RECORDED_VOICE = True

@csrf_exempt
def patient_ivr_callback(request, patient_id):
    """
    When we start a patient IVR interaction, we tell the tropo
    backend to call us back at this function when tropo makes a
    http call to us about it.  The data we pass is the patient_id.
    """
    
    patient = get_object_or_404(patients.Patient, pk=patient_id)

    # Got POST from Tropo wanting to know what to do
    try:
        logger.debug("##%s" % request.raw_post_data)
        postdata = json.loads(request.raw_post_data)
        
        if 'result' in postdata:
            # Survey result
            result = postdata['result']
            logger.debug("## Results=%r" % result)
            if 'error' in result and result['error'] is not None:
                logger.error("## Error from phone survey: %s" % result['error'])
            actions = result['actions']
            for item in actions:
                if item['name'].startswith('question'):
                    if item['disposition'] == 'SUCCESS':
                        # Got an answer, yay
                        # last char is a digit with question #
                        question_num = int(item['name'][-1])
                        # date would be today minus that many days
                        date = datetime.date.today()
                        date -= datetime.timedelta(days=question_num)
                        answer = item['value']
                        num_pills = int(answer)
                        # remember result
                        patients.remember_patient_pills_taken(patient, date,
                                                              num_pills, "IVR")
                    else:
                        logger.debug("## Error on question %s for patient: disposition %s" % (item['name'],item['disposition']))

            return http.HttpResponse()

        # New call, tell Tropo to run the survey
        our_callback_url = reverse('patient-ivr-complete', kwargs={'patient_id':patient_id})

        session = postdata['session']
        # Tell Tropo to call, ask questions, hang up

        # Need to tell Tropo explicitly that we want results back
        on1 = { 'on': {
            "next": our_callback_url,
            "event":"continue"}}
        on2 = { 'on': {
            "next": our_callback_url,
            "event":"error"}}
        on3 = { 'on': {
            "next": our_callback_url,
            "event":"hangup"}}
        on4 = { 'on': {
            "next": our_callback_url,
            "event":"incomplete"}}
        call = { 'call': {
            'to': patient.contact.default_connection.identity,
            'channel': 'VOICE',
            'name': patient_id,  # so we can correlate later
            }}

        if USE_RECORDED_VOICE:
            welcome_value = audio_file_url('01-Intro.mp3')
            ask_value = audio_file_url('02-HowManyDoses.mp3')
            thankyou_values = (audio_file_url('03-ThankYou.mp3'),
                              audio_file_url('04-YourAdherenceScoreIs.mp3'),
                              (u"%d" % patient.adherence()))
        else:
            welcome_value = "This is ARemind calling to see how you're doing."
            ask_value = 'How many pills did you miss in the last four days?  Please enter the number, then press pound.'
            thankyou_values = ("Thank you.  Your adherence is %d percent." % patient.adherence(),)

        # if call works, talk to them
        commands = [ on1, on2, on3, on4, call ]
        commands.append({ 'say': {
            'value': welcome_value,
            }})
        commands.append({ 'ask': {
            'say': { 'value': ask_value,
                     },
            'choices': { 'value': '[1-3 DIGITS]',
                         'mode': 'dtmf',
                         'terminator': '#'},
            'attempts': 3,
            'name': 'question1',
            }})
        for val in thankyou_values:
            commands.append({ 'say': {
            'value': val,
            }})
        commands.append({ 'hangup': None })

        to_return = { 'tropo': commands }
        logger.info("##Returning %s" % to_return)
        return http.HttpResponse(json.dumps(to_return))
    except Exception,e:
        logger.exception(e)
        return http.HttpResponseServerError()
        
@login_required
def patient_pill_report(request, patient_id):
    patient = get_object_or_404(patients.Patient, pk=patient_id)
    pills = patients.PatientPillsTaken.objects.filter(patient=patient).order_by('-date')
    context = {'patient': patient, 'pills': pills}
    return render(request, 'patients/patient_pill_report.html', context)


@login_required
def create_edit_pill_history(request, patient_id, pill_id=None):
    if pill_id:
        pill = get_object_or_404(patients.PatientPillsTaken, pk=pill_id, patient=patient_id)
        patient = pill.patient
    else:
        patient = get_object_or_404(patients.Patient, pk=patient_id)
        pill = patients.PatientPillsTaken(patient=patient)
    if request.method == 'POST':
        form = PillHistoryForm(request.POST, instance=pill)
        if form.is_valid():
            pill = form.save()
            messages.success(request, "Pill history saved.")
            return redirect('patient-report', patient_id)
    else:
        form = PillHistoryForm(instance=pill)
    context = {'patient': patient, 'pill': pill, 'form': form}
    return render(request, 'patients/create_edit_pill_history.html', context)
