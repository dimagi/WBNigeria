# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Reminder'
        db.create_table('adherence_reminder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('frequency', self.gf('django.db.models.fields.CharField')(default='daily', max_length=16, db_index=True)),
            ('weekdays', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=20, null=True, blank=True)),
            ('time_of_day', self.gf('django.db.models.fields.TimeField')()),
            ('date_last_notified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
        ))
        db.send_create_signal('adherence', ['Reminder'])

        # Adding M2M table for field recipients on 'Reminder'
        db.create_table('adherence_reminder_recipients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('reminder', models.ForeignKey(orm['adherence.reminder'], null=False)),
            ('contact', models.ForeignKey(orm['rapidsms.contact'], null=False))
        ))
        db.create_unique('adherence_reminder_recipients', ['reminder_id', 'contact_id'])

        # Adding model 'SendReminder'
        db.create_table('adherence_sendreminder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reminder', self.gf('django.db.models.fields.related.ForeignKey')(related_name='adherence_reminders', to=orm['adherence.Reminder'])),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='adherence_reminders', to=orm['rapidsms.Contact'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='queued', max_length=20)),
            ('date_queued', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_to_send', self.gf('django.db.models.fields.DateTimeField')()),
            ('date_sent', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=160)),
        ))
        db.send_create_signal('adherence', ['SendReminder'])


    def backwards(self, orm):
        
        # Deleting model 'Reminder'
        db.delete_table('adherence_reminder')

        # Removing M2M table for field recipients on 'Reminder'
        db.delete_table('adherence_reminder_recipients')

        # Deleting model 'SendReminder'
        db.delete_table('adherence_sendreminder')


    models = {
        'adherence.reminder': {
            'Meta': {'object_name': 'Reminder'},
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'date_last_notified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'frequency': ('django.db.models.fields.CharField', [], {'default': "'daily'", 'max_length': '16', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipients': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['rapidsms.Contact']", 'symmetrical': 'False'}),
            'time_of_day': ('django.db.models.fields.TimeField', [], {}),
            'weekdays': ('django.db.models.fields.CommaSeparatedIntegerField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        },
        'adherence.sendreminder': {
            'Meta': {'object_name': 'SendReminder'},
            'date_queued': ('django.db.models.fields.DateTimeField', [], {}),
            'date_sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_to_send': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'adherence_reminders'", 'to': "orm['rapidsms.Contact']"}),
            'reminder': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'adherence_reminders'", 'to': "orm['adherence.Reminder']"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'queued'", 'max_length': '20'})
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
