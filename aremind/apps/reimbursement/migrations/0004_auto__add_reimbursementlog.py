# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ReimbursementLog'
        db.create_table('reimbursement_reimbursementlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('amount', self.gf('django.db.models.fields.IntegerField')()),
            ('reimbursed_on', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('reimbursement', ['ReimbursementLog'])


    def backwards(self, orm):
        # Deleting model 'ReimbursementLog'
        db.delete_table('reimbursement_reimbursementlog')


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
            'reimbursed_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['reimbursement']