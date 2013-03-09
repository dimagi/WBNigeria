from django.contrib import admin

from aremind.apps.reimbursement.models import Batch, Reimbursement


class BatchAdmin(admin.ModelAdmin):
    list_display = ('count', 'last_time')

class ReimbursementAdmin(admin.ModelAdmin):
    list_display = ('batch', 'number', 'amount', 'network', 'status')

admin.site.register(Batch, BatchAdmin)
admin.site.register(Reimbursement, ReimbursementAdmin)
