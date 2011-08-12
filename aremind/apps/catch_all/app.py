from django.conf import settings
from rapidsms.apps.base import AppBase


class CatchAllApp(AppBase):
    """ RapidSMS app to reply to unhandled messages """

    template = getattr(settings, "DEFAULT_MESSAGE", "Thank you for contacting us.")

    def default(self, msg):
        """ If we reach the default phase here, always reply with help text """
        msg.respond(self.template)
        return True
