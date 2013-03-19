from django.contrib import admin

from aremind.apps.reimbursement.models import Batch, Reimbursement, Subscriber, ReimbursementRecord


class BatchAdmin(admin.ModelAdmin):
    list_display = ('count', 'last_time')

class ReimbursementAdmin(admin.ModelAdmin):
    list_display = ('batch', 'number', 'amount', 'network', 'status')

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('number', 'network', 'balance')

class ReimbursementRecordAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'amount', 'status', 'completed_on')

admin.site.register(Batch, BatchAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(ReimbursementRecord, ReimbursementRecordAdmin)
