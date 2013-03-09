# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Batch'
        db.create_table('reimbursement_batch', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_time', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
        ))
        db.send_create_signal('reimbursement', ['Batch'])

        # Adding model 'Reimbursement'
        db.create_table('reimbursement_reimbursement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('batch', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reimbursements', to=orm['reimbursement.Batch'])),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('amount', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('network', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('status', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('reimbursement', ['Reimbursement'])


    def backwards(self, orm):
        # Deleting model 'Batch'
        db.delete_table('reimbursement_batch')

        # Deleting model 'Reimbursement'
        db.delete_table('reimbursement_reimbursement')


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
            'network': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['reimbursement']