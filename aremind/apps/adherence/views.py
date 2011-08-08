import datetime
import logging

from django import http
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from aremind.apps.adherence.forms import (ReminderForm, FeedForm, EntryForm,
                                          QueryScheduleForm)
from aremind.apps.adherence.models import (Reminder, Feed, Entry,
                                           QuerySchedule, PatientSurvey,
                                           PillsMissed)
from aremind.apps.patients.models import Patient

logger = logging.getLogger('adherence.views')


@login_required
def dashboard(request):
    reminders = Reminder.objects.all().annotate(patient_count=Count('recipients'))
    feeds = Feed.objects.all().annotate(patient_count=Count('subscribers'))
    query_schedules = QuerySchedule.objects.all()
    context = {
        'reminders': reminders,
        'feeds': feeds,
        'query_schedules': query_schedules,
    }
    return render(request, 'adherence/dashboard.html', context)


@login_required
def create_edit_schedule(request, reminder_id=None):
    if reminder_id:
        reminder = get_object_or_404(Reminder, pk=reminder_id)
    else:
        reminder = Reminder()
    
    if request.method == 'POST':
        form = ReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            reminder = form.save()
            messages.info(request, "Reminder Schedule saved successfully")
            return redirect('adherence-dashboard')
    else:
        form = ReminderForm(instance=reminder)

    context = {
        'reminder': reminder,
        'form': form,
    }
    return render(request, 'adherence/create_edit_reminder.html', context)


@login_required
def delete_schedule(request, reminder_id):
    reminder = get_object_or_404(Reminder, pk=reminder_id)
    if request.method == 'POST':
        reminder.delete()
        messages.info(request, 'Reminder Schedule successfully deleted')
        return redirect('adherence-dashboard')
    context = {'reminder': reminder}
    return render(request, 'adherence/delete_reminder.html', context)


@login_required
def create_edit_feed(request, feed_id=None):
    if feed_id:
        feed = get_object_or_404(Feed, pk=feed_id)
    else:
        feed = Feed()
    
    if request.method == 'POST':
        form = FeedForm(request.POST, instance=feed)
        if form.is_valid():
            feed = form.save()
            messages.info(request, "Message Feed saved successfully")
            return redirect('adherence-dashboard')
    else:
        form = FeedForm(instance=feed)

    context = {
        'feed': feed,
        'form': form,
    }
    return render(request, 'adherence/create_edit_feed.html', context)


@login_required
def delete_feed(request, feed_id):
    feed = get_object_or_404(Feed, pk=feed_id)
    if request.method == 'POST':
        feed.delete()
        messages.info(request, 'Message Feed successfully deleted')
        return redirect('adherence-dashboard')
    context = {'feed': feed}
    return render(request, 'adherence/delete_feed.html', context)


@login_required
def view_feed(request, feed_id):
    feed = get_object_or_404(Feed, pk=feed_id)
    entries = feed.entries.all()
    context = {
        'feed': feed,
        'entries': entries,
    }
    return render(request, 'adherence/view_feed.html', context)


@login_required
def create_edit_entry(request, feed_id=None, entry_id=None):
    if entry_id:
        entry = get_object_or_404(Entry, pk=entry_id)
        feed = entry.feed
    elif feed_id:
        feed = get_object_or_404(Feed, pk=feed_id)
        entry = Entry(feed=feed)
    else:
        # Validated by url patterns
        raise http.Http404()

    if request.method == 'POST':
        form = EntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save()
            messages.info(request, "Message saved successfully")
            return redirect('adherence-dashboard')
    else:
        form = EntryForm(instance=entry)

    context = {
        'feed': feed,
        'entry': entry,
        'form': form,
    }
    return render(request, 'adherence/create_edit_entry.html', context)


@login_required
def delete_entry(request, entry_id):
    entry = get_object_or_404(Entry, pk=entry_id)
    if request.method == 'POST':
        entry.delete()
        messages.info(request, 'Message successfully deleted')
        return redirect('adherence-dashboard')
    context = {'entry': entry}
    return render(request, 'adherence/delete_entry.html', context)


@csrf_exempt
def ivr_callback(request):
    """Callback from tropo at end of an IVR dialog.
    (We asked tropo to call someone on the phone, talk to them, and
    get some answers, then visit this URL to give us the result.)
    """
    if request.GET['status'] == 'good':
        logger.info("Good IVR result: patient %s, answer %s" %
                    (request.GET['patient_id'], request.GET['answer']))
    else:
        logger.info("Bad IVR result: patient %s" % request.GET['patient_id'])
    return http.HttpResponse('')

@login_required
def query_results(request):
    context = {}
    context['results'] = PatientSurvey.objects.all().order_by('-last_modified')
    return render(request, 'adherence/query_results_report.html',
                  context)
    
@login_required
def create_edit_query_schedule(request, schedule_id=None):
    if schedule_id:
        schedule = get_object_or_404(QuerySchedule, pk=schedule_id)
    else:
        schedule = QuerySchedule()
    if request.method == 'POST':
        form = QueryScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.info(request, "Query schedule saved successfully")
            return redirect('adherence-dashboard')
    else:
        form = QueryScheduleForm(instance=schedule)

    context = {
        'form': form,
        'schedule': schedule,
    }
    return render(request, 'adherence/create_edit_query_schedule.html', context)

@login_required
def force_query_schedule(request, schedule_id):
    schedule = get_object_or_404(QuerySchedule, pk=schedule_id)
    schedule.start_scheduled_queries(force=True)
    return redirect('adherence-dashboard')

@login_required
def delete_query_schedule(request, schedule_id):
    schedule = get_object_or_404(QuerySchedule, pk=schedule_id)
    if request.method == 'POST':
        schedule.delete()
        messages.info(request, 'Query schedule successfully deleted')
        return redirect('adherence-dashboard')
    context = {'schedule':schedule}
    return render(request, 'adherence/delete_query_schedule.html', context)

@login_required
def pills_missed_report(request):
    pills_missed = PillsMissed.objects.order_by('-date')
    context = {'pills_missed': pills_missed }
    return render(request, 'adherence/pills_missed_report.html', context)

@login_required
def wisepill_not_reporting(request):
    hours48_ago = datetime.datetime.now() - datetime.timedelta(hours=48)
    notreporting = Patient.objects.all().exclude(wisepill_messages__timestamp__gte=hours48_ago).annotate(last_report=Max('wisepill_messages__timestamp'))
    context = { 'notreporting': notreporting }
    return render(request, 'adherence/wisepill_not_reporting.html', context)
