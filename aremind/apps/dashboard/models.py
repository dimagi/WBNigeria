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

    # site as determined by the keyword used to submit the report (PBF clinic, FUG, FCA (if not FUG specified))
    site = models.ForeignKey(Location)
    for_this_site = models.BooleanField(default=True) # False if report is not for the site it was reported from

    # free-form message provided with report
    freeform = models.CharField(max_length=200, null=True, blank=True)

    # whether report was reported on behalf of someone else (assume you cannot reach the original reporter)
    proxy = models.BooleanField()
    # whether reporter is ok to be contacted
    can_contact = models.BooleanField()

    # whether patient/beneficiary is satisfied
    satisfied = models.NullBooleanField()

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

    class Meta:
        permissions = (('pbf_view', 'View PBF reports'),)

class FadamaReport(FeedbackReport):
    # primary complaint type
    # complaint sub-type

    class Meta:
        permissions = (('fadama_view', 'View Fadama reports'),)


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
    author_user = models.ForeignKey('auth.User', null=True, blank=True)
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
            'contact_tags': sorted(contact.name for contact in self.contact_tags.all()),
        }

    def __unicode__(self):
        return u'{0} on Report {1} by {2} on {3}'.format(self.comment_type.title(),
                self.report.id, self.author, self.date.strftime('%Y-%m-%d %H:%M:%S'))


from smscouchforms.signals import xform_saved_with_session
from rapidsms_xforms.models import xform_received
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
        data['for_this_site'] = False
        content['site_other'] = form.get('different_fug_or_fca')
        data['freeform'] = form.get('describe_other_loc_problem')

        data['satisfied'] = None
    else:
        data['for_this_site'] = True
        data['satisfied'] = (form.get('project_phase2') == '1')
        if data['satisfied']:
            complaint_type = 'misc'
            complaint_subtype = 'misc'
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
                ['ldp', 'people', 'financial', 'serviceprovider', 'land', 'misc'],
                ['serviceprovider', 'people', 'info', 'misc']
            )

            subtypes = {
                'ldp': ('ldp', ['delay', 'other']),
                'people': ('people', ['state', 'community', 'facilitator', 'desk', 'other']),
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
                complaint_subtype = 'misc'

            if form.get('project_phase2_bad_sp_other'):
                data['freeform'] = form.get('project_phase2_bad_sp_other')

        content[complaint_type] = complaint_subtype

    data['can_contact'] = (form.get('contact') == '1')

    report = FadamaReport(**data)
    report.content = content
    return report

def pbf_report(form, data):
    data['schema_version'] = 1
    data['proxy'] = False
    content = {}

    if form.get('intro') != 'yes':
        data['for_this_site'] = False
        content['site_other'] = form.get('what_state')
        data['freeform'] = form.get('other_state_info')

        data['satisfied'] = None
        content['waiting_time'] = None
        content['staff_friendliness'] = None
        content['cleanliness'] = None
        content['drug_availability'] = None
        content['price_display'] = None
    else:
        data['for_this_site'] = True
        data['satisfied'] = (form.get('confirm_satisfied') == '1')
        data['freeform'] = form.get('other')

        content['waiting_time'] = {
            'less_two': 0,
            'two_to_four': 3,
            'more_four': 5,
        }.get(form.get('wait_time'))
        content['staff_friendliness'] = (form.get('friendly_staff') == '1')
        content['cleanliness'] = (form.get('hygiene') == '1')
        content['drug_availability'] = (form.get('drugs_available') == '1')
        content['price_display'] = (form.get('drugs_prices') == '1')

    data['can_contact'] = (form.get('contact_later') == '1')

    report = PBFReport(**data)
    report.content = content
    return report

def flat_yn(val):
    _val = val.lower()
    if _val not in ('y', 'n'):
        raise RuntimeError
    return (_val == 'y')

@receiver(xform_received, dispatch_uid='53qghbk38u3hl')
def on_flat_submit(sender, submission, xform, **args):
    if submission.has_errors:
        return

    processors = {
        'f3': fadama_report_flat,
        'cn': pbf_report_flat,
    }
    try:
        processor = processors[xform.keyword]
    except KeyError:
        return

    data = {
        'timestamp': datetime.now(),
        'reporter': submission.connection,
        'raw_report': submission.raw,
        'site': Location.objects.get(keyword=submission.template_vars['code']),
        'for_this_site': True,
        'proxy': True,
        'can_contact': False,
        'freeform': None,
        'satisfied': flat_yn(submission.template_vars['satisfied']),
    }

    report = processor(submission.template_vars, data)
    if report:
        report.save()

def fadama_report_flat(form, data):
    data['schema_version'] = 1

    from utils.fadama import COMPLAINT_TYPES, COMPLAINT_SUBTYPES
    type = COMPLAINT_TYPES[form['complaint_type'] - 1]
    subtype = COMPLAINT_SUBTYPES[type][form['complaint_subtype'] - 1]
    content = {type: subtype}

    report = FadamaReport(**data)
    report.content = content
    return report

def pbf_report_flat(form, data):
    data['schema_version'] = 1

    content = {
        'waiting_time': form['waiting_time'],
        'staff_friendliness': flat_yn(form['staff_friendliness']),
        'cleanliness': flat_yn(form['cleanliness']),
        'drug_availability': flat_yn(form['drug_availability']),
        'price_display': flat_yn(form['price_display']),
    }

    report = PBFReport(**data)
    report.content = content
    return report

