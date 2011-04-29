import datetime

from django.contrib import admin
from django.contrib import messages

from aremind.apps.patients import models as patients
from aremind.apps.patients.forms import PatientPayloadUploadForm
from aremind.apps.patients.importer import parse_payload


class PatientAdmin(admin.ModelAdmin):
    list_display = ('subject_number', 'date_enrolled', 'next_visit',
                    'mobile_number', 'pin', 'contact')
    list_filter = ('next_visit',)
    date_hierarchy = 'date_enrolled'
    ordering = ('-date_enrolled',)
    search_fields = ('subject_number', 'pin', 'mobile_number')
    raw_id_fields = ('raw_data', 'contact')
admin.site.register(patients.Patient, PatientAdmin)


class PatientDataPayloadAdmin(admin.ModelAdmin):
    list_display = ('id', 'submit_date', 'status')
    list_filter = ('status', 'submit_date', )
    search_fields = ('raw_data', )
    ordering = ('-submit_date', )
    add_form = PatientPayloadUploadForm
    add_fieldsets = (
        ('Upload a patient data file', {'fields': ('data_file', )}),
        ('Or paste in raw xml data', {'fields': ('raw_data', )}),
    )

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super(PatientDataPayloadAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during creation
        """
        defaults = {}
        if obj is None:
            defaults.update({'form': self.add_form})
        defaults.update(kwargs)
        return super(PatientDataPayloadAdmin, self).get_form(request, obj, **defaults)

    def save_model(self, request, obj, form, change):
        if not obj.submit_date:
            obj.submit_date = datetime.datetime.now()
        obj.save()
        try:
            parse_payload(obj)
        except Exception as e:
            messages.error(request, u"Error parsing patient data: %s" % unicode(e))
admin.site.register(patients.PatientDataPayload, PatientDataPayloadAdmin)
