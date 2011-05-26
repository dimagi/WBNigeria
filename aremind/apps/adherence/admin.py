from django.contrib import admin

from aremind.apps.adherence import models as adherence

admin.site.register(adherence.Reminder)
admin.site.register(adherence.SendReminder)
admin.site.register(adherence.Feed)
admin.site.register(adherence.Entry)
admin.site.register(adherence.EntrySeen)
admin.site.register(adherence.QuerySchedule)
admin.site.register(adherence.PatientSurvey)
