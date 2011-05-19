from rapidsms.apps.base import AppBase

from apps.wisepill.models import WisepillMessage

def looks_like_wisepill_message(text):
    # 
    return text.startswith("@=") and "SN=" in text \
           and "T=" in text \
           and "PC=" in text

class WisepillApp(AppBase):
    def start(self):
        self.info('started')

    def handle(self, msg):
        """Handle message that look like Wisepill messages"""
        self.critical('handle called')
        if not looks_like_wisepill_message(msg.text):
            self.info("does not look like a wisepill message, returning")
            return False

        self.info("got a wisepill message")
        wisepill_message = WisepillMessage(sms_message = msg.text)
        wisepill_message.save()
        return True # handled
