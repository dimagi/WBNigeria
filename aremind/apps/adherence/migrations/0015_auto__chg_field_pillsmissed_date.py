# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'PillsMissed.date'
        db.alter_column('adherence_pillsmissed', 'date', self.gf('django.db.models.fields.DateTimeField')())


    def backwards(self, orm):
        
        # Changing field 'PillsMissed.date'
        db.alter_column('adherence_pillsmissed', 'date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True))


    models = {
        'adherence.entry': {
            'Meta': {'ordering': "('-published',)", 'unique_together': "(('feed', 'uid'),)", 'object_name': 'Entry'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['adherence.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'percent_max': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'percent_min': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'uid': ('django.db.models.fields.CharField', [], {'default': "'1486f30344334e6db79ace67758a5c55'", 'max_length': '255'})
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_test': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'surveys'", 'to': "orm['patients.Patient']"}),
            'query_type': ('django.db.models.fields.IntegerField', [], {}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '-2'})
        },
        'adherence.pillsmissed': {
            'Meta': {'object_name': 'PillsMissed'},
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 1, 20, 15, 5, 35, 589000)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_missed': ('django.db.models.fields.IntegerField', [], {}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['patients.Patient']"}),
            'source': ('django.db.models.fields.IntegerField', [], {})
        },
        'adherence.queryschedule': {
            'Meta': {'object_name': 'QuerySchedule'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'days_between': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_run': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'patients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'adherence_query_schedules'", 'blank': 'True', 'to': "orm['patients.Patient']"}),
            'query_type': ('django.db.models.fields.IntegerField', [], {}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'adherence_query_schedules'", 'blank': 'True', 'to': "orm['groups.Group']"}),
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
            'batterystrength': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'unique': 'True'}),
            'daily_doses': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_enrolled': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2012, 1, 20)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual_adherence': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
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
