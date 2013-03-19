# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        # Note: Remember to use orm['appname.ModelName'] rather than "from appname.models..."
        for reimbursement in orm.Reimbursement.objects.filter(status=0):
            try:
                subscriber = orm.Subscriber.objects.get(number=reimbursement.number)
            except orm.Subscriber.DoesNotExist:
                subscriber = orm.Subscriber.objects.create(
                        number=reimbursement.number,
                        network=reimbursement.network,
                        balance=reimbursement.amount)
            else:
                subscriber.balance += reimbursement.amount
                subscriber.save()

    def backwards(self, orm):
        "Write your backwards methods here."

    models = {
        'reimbursement.batch': {
            'Meta': {'object_name': 'Batch'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'reimbursement.reimbursement': {
            'Meta': {'object_name': 'Reimbursement'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'batch': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reimbursements'", 'to': "orm['reimbursement.Batch']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'network': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        'reimbursement.reimbursementlog': {
            'Meta': {'object_name': 'ReimbursementLog'},
            'amount': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'reimbursed_on': ('django.db.models.fields.DateTimeField', [], {})
        },
        'reimbursement.subscriber': {
            'Meta': {'object_name': 'Subscriber'},
            'balance': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'network': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['reimbursement']
    symmetrical = True
