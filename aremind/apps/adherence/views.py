from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from aremind.apps.adherence.forms import ReminderForm
from aremind.apps.adherence.models import Reminder
from aremind.apps.patients.models import Patient



@login_required
def dashboard(request):
    reminders = Reminder.objects.all()
    context = {
        'reminders': reminders
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
