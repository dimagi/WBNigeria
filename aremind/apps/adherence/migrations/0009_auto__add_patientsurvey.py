# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PatientSurvey'
        db.create_table('adherence_patientsurvey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='surveys', to=orm['patients.Patient'])),
            ('query_type', self.gf('django.db.models.fields.IntegerField')()),
            ('created_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('started_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('completed_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=-2)),
        ))
        db.send_create_signal('adherence', ['PatientSurvey'])


    def backwards(self, orm):
        
        # Deleting model 'PatientSurvey'
        db.delete_table('adherence_patientsurvey')


    models = {
        'adherence.entry': {
            'Meta': {'ordering': "('-published',)", 'unique_together': "(('feed', 'uid'),)", 'object_name': 'Entry'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['adherence.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'uid': ('django.db.models.fields.CharField', [], {'default': "'46a88945b23045edb6ae312cb3071e48'", 'max_length': '255'})
        },
        'adherence.entryseen': {
            'Meta': {'unique_together': "(('entry', 'patient'),)", 'object_name': 'EntrySeen'},
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['adherence.Entry']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries_seen'", 'to': "orm['patients.Patient']"})
        },
        'adherence.feed': {
            'Meta': {'object_name': 'Feed'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'feed_type': ('django.db.models.fields.CharField', [], {'default': "'manual'", 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_download': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'subscribers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'feeds'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'adherence.patientsurvey': {
            'Meta': {'object_name': 'PatientSurvey'},
            'completed_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'created_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'surveys'", 'to': "orm['patients.Patient']"}),
            'query_type': ('django.db.models.fields.IntegerField', [], {}),
            'started_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '-2'})
        },
        'adherence.queryschedule': {
            'Meta': {'object_name': 'QuerySchedule'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'days_between': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'query_type': ('django.db.models.fields.IntegerField', [], {}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'adherence_query_schedules'", 'symmetrical': 'False', 'to': "orm['groups.Group']"}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'time_of_day': ('django.db.models.fields.TimeField', [], {})
        },
        'adherence.reminder': {
            'Meta': {'object_name': 'Reminder'},
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_last_notified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'frequency': ('django.db.models.fields.CharField', [], {'default': "'daily'", 'max_length': '16', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'reminders'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'time_of_day': ('django.db.models.fields.TimeField', [], {}),
            'weekdays': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'adherence.sendreminder': {
            'Meta': {'object_name': 'SendReminder'},
            'date_queued': ('django.db.models.fields.DateTimeField', [], {}),
            'date_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_to_send': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '160', 'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'adherence_reminders'", 'to': "orm['rapidsms.Contact']"}),
            'reminder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'adherence_reminders'", 'to': "orm['adherence.Reminder']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'queued'", 'max_length': '20'})
        },
        'groups.group': {
            'Meta': {'object_name': 'Group'},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_editable': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'patients.patient': {
            'Meta': {'object_name': 'Patient'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'unique': 'True'}),
            'daily_doses': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_enrolled': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2011, 5, 26)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'next_visit': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'raw_data': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'patients'", 'null': 'True', 'to': "orm['patients.PatientDataPayload']"}),
            'reminder_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'wisepill_msisdn': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'})
        },
        'patients.patientdatapayload': {
            'Meta': {'object_name': 'PatientDataPayload'},
            'error_message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raw_data': ('django.db.models.fields.TextField', [], {}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'received'", 'max_length': '16'}),
            'submit_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'primary_backend': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'contact_primary'", 'null': 'True', 'to': "orm['rapidsms.Backend']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }

    complete_apps = ['adherence']
