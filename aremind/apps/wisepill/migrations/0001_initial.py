# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'WisepillMessage'
        db.create_table('wisepill_wisepillmessage', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sms_message', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('time_received', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('message_type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('msisdn', self.gf('django.db.models.fields.CharField')(max_length=12)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
        ))
        db.send_create_signal('wisepill', ['WisepillMessage'])


    def backwards(self, orm):
        
        # Deleting model 'WisepillMessage'
        db.delete_table('wisepill_wisepillmessage')


    models = {
        'wisepill.wisepillmessage': {
            'Meta': {'object_name': 'WisepillMessage'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_type': ('django.db.models.fields.SmallIntegerField', [], {}),
            'msisdn': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'sms_message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'time_received': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['wisepill']
