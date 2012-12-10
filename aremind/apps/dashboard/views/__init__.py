from django.http import HttpResponse
from django.shortcuts import render
from pbf import *
from fadama import *

def landing(request):
    return render(request, 'dashboard/base.html', {'shownav': True})
