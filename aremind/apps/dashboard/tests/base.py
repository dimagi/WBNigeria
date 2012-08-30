import datetime

from rapidsms.contrib.locations.models import Location

from aremind.apps.dashboard.models import ReportComment, FadamaReport
from aremind.tests.testcases import CreateDataTest


class DashboardDataTest(CreateDataTest):
    "Helpers to create dashboard related data."

    def create_feedback_report(self, cls=FadamaReport, **kwargs):
        "Random test feedback report."
        defaults = {
            'timestamp': datetime.datetime.now(),
            'proxy': False,
            'can_contact': True,
            'satisfied': True,
            'schema_version': 1,
            'raw_report': self.random_unicode_string()            
        }
        defaults.update(kwargs)
        if 'reporter' not in defaults:
            defaults['reporter'] = self.create_connection()
        if 'site' not in defaults:
            defaults['site'] = Location.objects.create()
        return cls.objects.create(**defaults)

    def create_report_comment(self, **kwargs):
        "Feedback comment on a report."
        defaults = {
            'comment_type': ReportComment.INQUIRY_TYPE,
            'author': 'staff',
            'text': self.random_unicode_string(),         
        }
        defaults.update(kwargs)
        if 'report' not in defaults:
            defaults['report'] = self.create_feedback_report()
        return ReportComment.objects.create(**defaults)
