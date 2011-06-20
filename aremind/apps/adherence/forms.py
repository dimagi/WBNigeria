from django import forms

from rapidsms.models import Contact

from aremind.apps.adherence.models import Reminder, Feed, Entry, QuerySchedule


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

    percent_max = forms.IntegerField(required=False, max_value=100, min_value=0)
    percent_min = forms.IntegerField(required=False, max_value=100, min_value=0)


    class Meta(object):
        model = Entry
        fields = ('content', 'published', 'percent_max', 'percent_min', )

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        self.fields['published'].widget.attrs.update({'class': 'datetimepicker'})
        if self.instance and self.instance.feed:
            feed = self.instance.feed
            if feed.feed_type != Feed.TYPE_MANUAL:
                del self.fields['percent_max']
                del self.fields['percent_min']

    def clean(self):
        super(EntryForm, self).clean()
        if self.instance and self.instance.feed:
            feed = self.instance.feed
            if feed.feed_type != Feed.TYPE_MANUAL:
                self.cleaned_data['percent_max'] = None 
                self.cleaned_data['percent_min'] = None
        percent_max = self.cleaned_data.get('percent_max', None)
        percent_min = self.cleaned_data.get('percent_min', None)
        if percent_max and percent_min and percent_min > percent_max:
            raise forms.ValidationError('Max adherence percentage much be greater than min.')
        return self.cleaned_data
            

class QueryScheduleForm(forms.ModelForm):
    class Meta(object):
        model = QuerySchedule

    def __init__(self, *args, **kwargs):
        super(QueryScheduleForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].label = 'Start date'
        self.fields['start_date'].required = True
        self.fields['start_date'].widget.attrs['class'] = 'datepicker'
        self.fields['time_of_day'].widget.attrs['class'] = 'timepicker'
