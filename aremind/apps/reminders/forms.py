from django import forms
from django.conf import settings
from django.forms.models import modelformset_factory

from rapidsms.models import Contact

from aremind.apps.groups.models import Group
from aremind.apps.groups.validators import validate_phone
from aremind.apps.groups.utils import normalize_number
from aremind.apps.reminders import models as reminders


NotificationFormset = modelformset_factory(reminders.Notification,
                                           can_delete=True)

class NotificationForm(forms.ModelForm):

    class Meta(object):
        model = reminders.Notification


class ReportForm(forms.Form):
    date = forms.DateField(label='Report Date', required=False)
    date.widget.attrs.update({'class': 'datepicker'})

class MonthReportForm(forms.Form):
    date = forms.DateField(label='Report Date', required=False)
    date.widget.attrs.update({'class': 'monthpicker'})
    fakedate = forms.CharField()
    fakedate.widget.attrs.update({'class': 'fakedate'})
