# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Patient.manual_adherence'
        db.add_column('patients_patient', 'manual_adherence', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Patient.manual_adherence'
        db.delete_column('patients_patient', 'manual_adherence')


    models = {
        'patients.patient': {
            'Meta': {'object_name': 'Patient'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'unique': 'True'}),
            'daily_doses': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'date_enrolled': ('django.db.models.fields.DateField', [], {'default': 'datetime.date(2011, 5, 26)'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manual_adherence': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
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
        'patients.patientpillstaken': {
            'Meta': {'object_name': 'PatientPillsTaken'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'num_pills': ('django.db.models.fields.IntegerField', [], {}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['patients.Patient']"})
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

    complete_apps = ['patients']
