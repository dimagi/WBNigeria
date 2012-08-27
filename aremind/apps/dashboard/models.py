from django.db import models
from rapidsms.models import Connection
from rapidsms.contrib.locations.models import Location, LocationType
import json
from datetime import datetime

class FeedbackReport(models.Model):

    # when report was received
    timestamp = models.DateTimeField()

    # rapidsms contact report came from
    reporter = models.ForeignKey(Connection)

    # site report is in reference to (PBF clinic, FUG, FCA (if no FUG specified)
    # TODO need to handle no site specified?
    site = models.ForeignKey(Location)

    # free-form message provided with report
    freeform = models.CharField(max_length=200, null=True, blank=True)

    # whether report was reported on behalf of someone else (assume you cannot reach the original reporter)
    proxy = models.BooleanField()

    # whether patient/beneficiary is satisfied
    satisfied = models.BooleanField()

    # json data of report contents
    data = models.TextField(null=True, blank=True)

    # incrementing version number for the form data schema
    schema_version = models.IntegerField()

    # uuid of raw report data in couchdb
    raw_report = models.TextField()

    @property
    def content(self):
        return json.loads(self.data) if self.data else {}

    @content.setter
    def content(self, value):
        self.data = json.dumps(value) if value is not None else None

    class Meta:
        abstract = True

class PBFReport(FeedbackReport):
    # waiting time
    # staff friendliness
    # prices displayed
    # drug availability
    # cleanliness
    pass

class FadamaReport(FeedbackReport):
    # primary complaint type
    # complaint sub-type
    pass


class ReportComment(models.Model):
    INQUIRY_TYPE = 'inquiry'
    NOTE_TYPE = 'note'
    REPLY_TYPE = 'response'

    FROM_BENEFICIARY = '_bene'

    COMMENT_TYPES = (
        (INQUIRY_TYPE, INQUIRY_TYPE),
        (NOTE_TYPE, NOTE_TYPE),
        (REPLY_TYPE, REPLY_TYPE),
    )

    report = models.ForeignKey(FadamaReport)
    comment_type = models.CharField(max_length=50, choices=COMMENT_TYPES)
    author = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    extra_info = models.TextField(null=True, blank=True)

    def json(self):
        return {
            'id': self.id,
            'text': self.text,
            'date_fmt': self.date.strftime('%d/%m/%Y %H:%M'),
            'author': self.author,
            'report_id': self.report.id,
            'type': self.comment_type,
            'extra': json.loads(self.extra_info) if self.extra_info else None,
        }







from smscouchforms.signals import xform_saved_with_session
from django.dispatch import receiver

@receiver(xform_saved_with_session)
def on_form_submit(sender, session, xform, **kwargs):
    reporter = session.connection
    reg_code = session.trigger.trigger_keyword
    form = xform.get_form
    doc_id = xform.get_id

    # TODO make a setting?
    processors = {
        'http://openrosa.org/formdesigner/Fadama': fadama_report,
        'http://openrosa.org/formdesigner/PBF-FORM': pbf_report,
    }

    data = {
        'timestamp': datetime.now(),
        'reporter': reporter,
        'raw_report': doc_id,
        'site': Location.objects.get(id=int(form['site_id'])),
    }
    try:
        processor = processors[form['@xmlns']]
    except KeyError:
        # not a form type we care about
        return

    report = processor(form, data)
    report.save()

def fadama_report(form, data):
    print form, data

def pbf_report(form, data):
    pass
