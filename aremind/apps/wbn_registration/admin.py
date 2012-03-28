from django.contrib import admin
from django.contrib import messages
from models import WBUser


class WBUserAdmin(admin.ModelAdmin):
    list_display = ('date_registered', 'connection','is_registered', 'location_code', 'survey_question_ans', 'want_more_surveys')
admin.site.register(WBUser, WBUserAdmin)
