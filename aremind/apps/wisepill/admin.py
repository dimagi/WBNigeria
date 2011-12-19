from django.contrib import admin

from aremind.apps.wisepill import models as wisepill

class WisepillMessageAdmin(admin.ModelAdmin):
    list_display = ('sms_message','patient', 'message_type', 'time_received', 'timestamp')

admin.site.register(wisepill.WisepillMessage, WisepillMessageAdmin)
