from django.db import models
from rapidsms.models import Connection, Contact
from rapidsms.contrib.locations.models import Location, LocationType
import json
from datetime import datetime
from django.conf import settings

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
    # whether reporter is ok to be contacted
    can_contact = models.BooleanField()

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
    contact_tags = models.ManyToManyField(Contact, related_name='comment_tags',
            blank=True, null=True)

    def json(self):
        return {
            'id': self.id,
            'text': self.text,
            'date_fmt': self.date.strftime('%d/%m/%Y %H:%M'),
            'author': self.author,
            'report_id': self.report.id,
            'type': self.comment_type,
            'extra': json.loads(self.extra_info) if self.extra_info else None,
            'contact_tags': [contact.id for contact in self.contact_tags.all()],
        }


from smscouchforms.signals import xform_saved_with_session
from django.dispatch import receiver

@receiver(xform_saved_with_session, dispatch_uid='cnru057m2ccbn')
def on_form_submit(sender, session, xform, **kwargs):
    reporter = session.connection
    reg_code = session.trigger.trigger_keyword
    form = xform.get_form
    doc_id = xform.get_id

    data = {
        'timestamp': datetime.now(),
        'reporter': reporter,
        'raw_report': doc_id,
        'site': Location.objects.get(id=int(form['site_id'])),
    }

    processors = {
        'fadama': fadama_report,
        'pbf': pbf_report,
    }
    try:
        form_type = dict((v, k) for k, v in settings.DECISION_TREE_FORMS.iteritems())[form['@xmlns']]
        processor = processors[form_type]
    except KeyError:
        # not a form type we care about
        return

    report = processor(form, data)
    if report:
        report.save()

def fadama_report(form, data):
    data['schema_version'] = 1
    data['proxy'] = False
    content = {}

    if form.get('confirm_location') == '2':
        data['site'] = None
        # what about:
        #   different_fug_or_fca 'what is your site?'
        #   describe_other_loc_problem 'what is your problem at the other site?'
    else:
        data['satisfied'] = (form.get('project_phase2') == '1')
        if data['satisfied']:
            complaint_type = None
            complaint_subtype = None
            data['freeform'] = 'What is good: %s; Could be improved: %s' % (form.get('project_phase2_good'), form.get('project_phase2_improved'))
        else:
            def get_enum(field, choices):
                try:
                    return choices[int(form.get(field)) - 1]
                except (ValueError, TypeError, IndexError):
                    return None

            def get_combo_enum(field, choices1, choices2=None):
                if field:
                    field = '_' + field
                else:
                    field = ''

                result = get_enum('project_phase1_bad%s' % field, choices1)
                if not result:
                    result = get_enum('project_phase2_bad%s' % field, choices2 or choices1)
                return result

            data['freeform'] = form.get('project_phase2_bad_sp_default')

            complaint_type = get_combo_enum(None,
                ['ldp', 'people', 'financial', 'serviceprovider', 'land', 'other'],
                ['serviceprovider', 'people', 'info', 'other']
            )

            subtypes = {
                'ldp': ('ldp', ['delay', 'other']),
                'people': ('people', ['state', 'fug', 'facilitator', 'desk', 'other']), # no fca? 'desk' is new
                'financial': ('money', ['bank', 'delay', 'other']),
                'serviceprovider': ('sp', ['notfind', 'other'], ['notstarted', 'delay', 'stopped', 'substandard', 'other']),
                'land': ('land', ['notfind', 'suitability', 'ownership', 'other']),
                'info': ('info', ['input', 'market', 'credit', 'other']),
            }.get(complaint_type)
            if subtypes:
                try:
                    field, phase1choices = subtypes
                    phase2choices = None
                except (ValueError, TypeError):
                    field, phase1choices, phase2choices = subtypes

                complaint_subtype = get_combo_enum(field, phase1choices, phase2choices)

            else:
                complaint_subtype = None
                
            if form.get('project_phase2_bad_sp_other'):
                content['other_detail'] = form.get('project_phase2_bad_sp_other')

        if complaint_type:
            content[complaint_type] = complaint_subtype

    data['can_contact'] = (form.get('contact') == '1')

    # filter out types of reports the dashboard can't handle yet
    if data['site'] is None:
        return
    if not set(content.keys()) - set(['other_detail']):
        return

    report = FadamaReport(**data)
    report.content = content
    return report

def pbf_report(form, data):
    pass

