# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ReportComment'
        db.create_table('dashboard_reportcomment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('report_id', self.gf('django.db.models.fields.IntegerField')()),
            ('comment_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('dashboard', ['ReportComment'])


    def backwards(self, orm):
        # Deleting model 'ReportComment'
        db.delete_table('dashboard_reportcomment')


    models = {
        'dashboard.reportcomment': {
            'Meta': {'object_name': 'ReportComment'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'comment_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report_id': ('django.db.models.fields.IntegerField', [], {}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['dashboard']