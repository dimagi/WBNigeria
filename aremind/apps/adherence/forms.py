from django import forms

from rapidsms.models import Contact

from aremind.apps.adherence.models import Reminder, Feed, Entry


class ReminderForm(forms.ModelForm):

    weekdays = forms.MultipleChoiceField(choices=Reminder.WEEKDAY_CHOICES, widget=forms.CheckboxSelectMultiple)

    class Meta(object):
        model = Reminder
        fields = ('frequency', 'weekdays', 'time_of_day', 'recipients', )

    def __init__(self, *args, **kwargs):
        super(ReminderForm, self).__init__(*args, **kwargs)
        self.fields['time_of_day'].widget.attrs.update({'class': 'timepicker'})

        self.fields['recipients'].widget.attrs.update({'class': 'multiselect'})
        self.fields['recipients'].help_text = u''       
        qs = Contact.objects.filter(patient__isnull=False).order_by('patient__subject_number')
        self.fields['recipients'].queryset = qs
        self.fields['recipients'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        return obj.patient_set.all()[0].subject_number

    def clean_weekdays(self):
        weekdays = self.cleaned_data.get('weekdays', [])
        return u','.join(weekdays)

    def clean(self):
        super(ReminderForm, self).clean()
        frequency = self.cleaned_data.get('frequency', None)
        if frequency and frequency == Reminder.REPEAT_DAILY:
            self.cleaned_data['weekdays'] = None
            if 'weekdays' in self._errors:
                del self._errors['weekdays']
        return self.cleaned_data


class FeedForm(forms.ModelForm):

    class Meta(object):
        model = Feed
        fields = ('name', 'feed_type', 'url', 'description', 'subscribers', 'active', )
    
    def __init__(self, *args, **kwargs):
        super(FeedForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget = forms.Textarea()
        self.fields['subscribers'].widget.attrs.update({'class': 'multiselect'})
        self.fields['subscribers'].help_text = u''       
        qs = Contact.objects.filter(patient__isnull=False).order_by('patient__subject_number')
        self.fields['subscribers'].queryset = qs
        self.fields['subscribers'].label_from_instance = self.label_from_instance

    def label_from_instance(self, obj):
        return obj.patient_set.all()[0].subject_number


class EntryForm(forms.ModelForm):

    class Meta(object):
        model = Entry
        fields = ('content', 'published', )

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['published'].widget.attrs.update({'class': 'datetimepicker'})

