from django.shortcuts import render, redirect

from aremind.apps.patients.models import Patient


def dashboard(request):
    patients = Patient.objects.all().select_related('contact', 'contact__reminders')
    context = {
        'patients': patients
    }
    return render(request, 'adherence/dashboard.html', context)
