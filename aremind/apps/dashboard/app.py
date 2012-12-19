from rapidsms.apps.base import AppBase
from aremind.apps.dashboard.models import FadamaReport, ReportComment
from datetime import datetime
from django.conf import settings
import json
from notifications.communicator_response import trigger_alerts

# for debugging
from apps.dashboard.utils.fadama import load_reports
from apps.utils.functional import map_reduce

class CommunicatorApp(AppBase):
    "Catch messages which might be replies to messages sent by the dashboard communicator."

    def handle(self, msg):
        "Handle otherwise unhandled message from users related to inquiry messages."
        active_reports = active_communicator_threads(msg.connection.identity)
        if not active_reports:
            return False

        for active_report in active_reports:
            comment_data = {
                'fadama_report_id': active_report,
                'comment_type': ReportComment.REPLY_TYPE,
                'text': msg.text,
                'author': ReportComment.FROM_BENEFICIARY,
            }
            if len(active_reports) > 1:
                comment_data['extra_info'] = json.dumps({'ambiguous': list(set(active_reports) - set([active_report]))})

            response = ReportComment.objects.create(**comment_data)
            trigger_alerts(FadamaReport.objects.get(id=active_report), response)

        # TODO: reply back here? 'your response is received'
        return True
            

def active_communicator_threads(phone_number):
    "Return all phone numbers tied to a submitted report."
    # todo make this query more efficient one we've settled on a back-end data model
    comments = ReportComment.objects.filter(
        comment_type=ReportComment.INQUIRY_TYPE,
        fadama_report__reporter__identity=phone_number,
    )
    latest_inquiry_per_report = map_reduce(comments, lambda c: [(c.report.id, c.date)], lambda v, k: max(v))
    active_report_ids = [report_id for report_id, last_inquiry in latest_inquiry_per_report.iteritems() if datetime.now() - last_inquiry < settings.COMMUNICATOR_RESPONSE_WINDOW]
    return active_report_ids

