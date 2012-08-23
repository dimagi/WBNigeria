from django.db import models
from rapidsms.models import Connection
from rapidsms.contrib.locations.models import Location, LocationType
import json

class FeedbackReport(models.Model):

    # when report was received
    timestamp = models.DateTimeField()

    # rapidsms contact report came from
    reporter = models.ForeignKey(Connection)

    # site report is in reference to (PBF clinic, FUG, FCA (if no FUG specified), need to handle no site specified?)
    site = models.ForeignKey(Location)

    # free-form message provided with report
    freeform = models.CharField(max_length=200, null=True, blank=True)

    # whether report was reported on behalf of someone else (assume you cannot reach the original reporter)
    proxy = models.BooleanField()

    # whether patient/beneficiary is satisfied
    satisfied = models.BooleanField()

    # json data of report contents
    data = models.TextField(null=True, blank=True)

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

