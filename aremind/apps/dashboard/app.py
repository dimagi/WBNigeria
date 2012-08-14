from rapidsms.apps.base import AppBase

from aremind.apps.dashboard.models import ReportComment
from aremind.apps.dashboard.utils.fadama import get_inquiry_numbers


class CommunicatorApp(AppBase):
    "Catch messages which might be replies to messages sent by the dashboard communicator."

    def handle(self, msg):
        "Handle otherwise unhandled message from users related to inquiry messages."
        if msg.connection.identity in get_inquiry_numbers():
            comment_data = {
                'report_id': None,
                'comment_type': ReportComment.REPLY_TYPE,
                'text': msg.text,
                #TODO: Should this be the phone # instead?
                'author': 'beneficiary',
            }
            # Create a report comment
            ReportComment.objects.create(**comment_data)
            # TODO: Add a reply?
            return True
        else:
            return False
            
