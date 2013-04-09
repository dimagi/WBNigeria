from django.contrib import admin

from aremind.apps.reimbursement.models import Batch, Reimbursement, Subscriber, ReimbursementRecord, ReimbursementLog
from datetime import datetime


class BatchAdmin(admin.ModelAdmin):
    list_display = ('count', 'last_time')

class ReimbursementAdmin(admin.ModelAdmin):
    list_display = ('batch', 'number', 'amount', 'network', 'status')

class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('number', 'network', 'balance')
    search_fields = ('number',)

class ReimbursementRecordAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'network', 'amount', 'status', 'completed_on')

    def save_model(self, request, obj, form, change):
        obj.completed_on = datetime.now()
        obj.messages = 'Manual reimbursement by %s'%request.user.username
        obj.save()
        if not change:
            ReimbursementLog.objects.create(
                    phone='+234%s'%obj.subscriber.number[-10:],
                    amount=obj.amount,
                    reimbursed_on=datetime.now())

admin.site.register(Batch, BatchAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(ReimbursementRecord, ReimbursementRecordAdmin)
