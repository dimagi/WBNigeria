from django import forms
from django.forms.models import modelformset_factory

from rapidsms.models import Contact
from selectable.forms import AutoComboboxSelectMultipleField

from aremind.apps.adherence.lookups import ReminderLookup, FeedLookup
from aremind.apps.groups.forms import FancyPhoneInput
from aremind.apps.groups.validators import validate_phone
from aremind.apps.groups.utils import normalize_number
from aremind.apps.patients import models as patients


XML_DATE_FORMATS = ('%b  %d %Y ',)
XML_TIME_FORMATS = ('%H:%M', )

class PatientForm(forms.ModelForm):

    date_enrolled = forms.DateField(input_formats=XML_DATE_FORMATS)
    next_visit = forms.DateField(input_formats=XML_DATE_FORMATS,
                                 required=False)
    reminder_time = forms.TimeField(input_formats=XML_TIME_FORMATS,
                                    required=False)

    class Meta(object):
        model = patients.Patient
        exclude = ('raw_data', 'contact')

    def clean_mobile_number(self):
        mobile_number = normalize_number(self.cleaned_data['mobile_number'])
        validate_phone(mobile_number)
        return mobile_number

    def save(self, payload):
        instance = super(PatientForm, self).save(commit=False)
        instance.raw_data = payload
        instance.raw_data.status = 'success'
        instance.raw_data.save()
        # get or create associated contact record
        if not instance.contact_id:
            subject_number = instance.subject_number
            contact, _ = Contact.objects.get_or_create(name=subject_number)
            instance.contact = contact
        instance.contact.phone = instance.mobile_number
        instance.contact.pin = instance.pin
        instance.contact.save()
        instance.save()
        return instance


class PatientPayloadUploadForm(forms.ModelForm):
    data_file = forms.FileField(required=False)

    class Meta(object):
        model = patients.PatientDataPayload
        fields = ('raw_data', )

    def __init__(self, *args, **kwargs):
        super(PatientPayloadUploadForm, self).__init__(*args, **kwargs)
        self.fields['raw_data'].required = False

    def clean(self):
        raw_data = self.cleaned_data.get('raw_data', '')
        data_file = self.cleaned_data.get('data_file', None)
        if not (raw_data or data_file):
            raise forms.ValidationError('You must either upload a file or include raw data.')
        if data_file and not raw_data:
            self.cleaned_data['raw_data'] = data_file.read()
        return self.cleaned_data


class PatientRemindersForm(forms.ModelForm):

    reminders = AutoComboboxSelectMultipleField(ReminderLookup, label="Medicine Reminders", required=False)
    feeds = AutoComboboxSelectMultipleField(FeedLookup, required=False)

    class Meta(object):
        model = patients.Patient
        fields = ('subject_number', 'mobile_number', 'pin', 'next_visit', 'reminder_time', )

    def __init__(self, *args, **kwargs):
        super(PatientRemindersForm, self).__init__(*args, **kwargs)
        self.fields['mobile_number'].widget = FancyPhoneInput()
        self.fields['next_visit'].widget.attrs.update({'class': 'datepicker'})
        self.fields['reminder_time'].widget.attrs.update({'class': 'timepicker'})
        self.fields['reminder_time'].label = 'Appointment Reminder Time'
        if self.instance and self.instance.pk:
            self.initial['reminders'] = self.instance.contact.reminders.all()
            self.initial['feeds'] = self.instance.contact.feeds.all()

    def save(self, *args, **kwargs):
        patient = super(PatientRemindersForm, self).save(commit=False)
        if not patient.contact_id:            
            contact, _ = Contact.objects.get_or_create(name=patient.subject_number)
            patient.contact = contact
        patient.contact.phone = patient.mobile_number
        patient.contact.pin = patient.pin
        commit = kwargs.pop('commit', True)
        if commit:
            reminders = self.cleaned_data.get('reminders', []) or []
            patient.contact.reminders.clear()
            for r in reminders:
                r.recipients.add(patient.contact)
            feeds = self.cleaned_data.get('feeds', []) or []
            patient.contact.feeds.clear()
            for f in feeds:
                f.subscribers.add(patient.contact)
            patient.contact.save()
            patient.save()
        return patient


class PatientOnetimeMessageForm(forms.Form):
    message = forms.CharField(label="Message", max_length=140, min_length=1, 
                              widget=forms.Textarea)
    
