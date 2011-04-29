# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'PatientDataPayload'
        db.create_table('patients_patientdatapayload', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('raw_data', self.gf('django.db.models.fields.TextField')()),
            ('submit_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.CharField')(default='received', max_length=16)),
            ('error_message', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('patients', ['PatientDataPayload'])

        # Adding model 'Patient'
        db.create_table('patients_patient', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('raw_data', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='patients', null=True, to=orm['patients.PatientDataPayload'])),
            ('contact', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patients', unique=True, to=orm['rapidsms.Contact'])),
            ('subject_number', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('date_enrolled', self.gf('django.db.models.fields.DateField')()),
            ('mobile_number', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('pin', self.gf('django.db.models.fields.CharField')(max_length=4, blank=True)),
            ('next_visit', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('reminder_time', self.gf('django.db.models.fields.TimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('patients', ['Patient'])


    def backwards(self, orm):
        
        # Deleting model 'PatientDataPayload'
        db.delete_table('patients_patientdatapayload')

        # Deleting model 'Patient'
        db.delete_table('patients_patient')


    models = {
        'patients.patient': {
            'Meta': {'object_name': 'Patient'},
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patients'", 'unique': 'True', 'to': "orm['rapidsms.Contact']"}),
            'date_enrolled': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile_number': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'next_visit': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '4', 'blank': 'True'}),
            'raw_data': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'patients'", 'null': 'True', 'to': "orm['patients.PatientDataPayload']"}),
            'reminder_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'subject_number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
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

    complete_apps = ['patients']
