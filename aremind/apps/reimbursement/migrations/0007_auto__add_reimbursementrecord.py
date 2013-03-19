# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ReimbursementRecord'
        db.create_table('reimbursement_reimbursementrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subscriber', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['reimbursement.Subscriber'])),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('status', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('messages', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('reimbursement', ['ReimbursementRecord'])


    def backwards(self, orm):
        # Deleting model 'ReimbursementRecord'
        db.delete_table('reimbursement_reimbursementrecord')


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
        'reimbursement.reimbursementrecord': {
            'Meta': {'object_name': 'ReimbursementRecord'},
            'amount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'messages': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'subscriber': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['reimbursement.Subscriber']"})
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