# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'ReportComment.report_id'
        db.alter_column('dashboard_reportcomment', 'report_id', self.gf('django.db.models.fields.IntegerField')(null=True))

    def backwards(self, orm):

        # Changing field 'ReportComment.report_id'
        db.alter_column('dashboard_reportcomment', 'report_id', self.gf('django.db.models.fields.IntegerField')(default=0))

    models = {
        'dashboard.reportcomment': {
            'Meta': {'object_name': 'ReportComment'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'comment_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'report_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['dashboard']