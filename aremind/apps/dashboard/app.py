import re

from rapidsms.apps.base import AppBase

from aremind.apps.dashboard.models import ReportComment


class CommunicatorApp(AppBase):
    "Catch messages which are replies to messages sent by the dashboard communicator."

    reply_id_regex = re.compile(r'\bR(?P<report_id>\d+)\b')

    def handle(self, msg):
        "Match incoming messages to the reply ID format."
        match = self.reply_id_regex.search(msg.text)
        if match:
            report_id = match.groupdict()['report_id']
            # TODO: Might need to validate that this number is related to this report
            comment_data = {
                'report_id': report_id,
                'comment_type': ReportComment.REPLY_TYPE,
                'text': self.reply_id_regex.sub('', msg.text),
                #TODO: Should this be the phone # instead?
                'author': 'beneficiary',
            }
            # Create a report comment
            ReportComment.objects.create(**comment_data)
            # TODO: Add a reply?
            return True
        else:
            return False
            
