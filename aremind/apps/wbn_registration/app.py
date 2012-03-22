from django.core.exceptions import ObjectDoesNotExist
from rapidsms.apps.base import AppBase
from touchforms.formplayer import api
from touchforms.formplayer.models import XForm
from models import WBUser
import logging
import json
import os

LOCATIONS_FILE = 'locations.json'

# In RapidSMS, message translation is done in OutgoingMessage, so no need
# to attempt the real translation here.  Use _ so that ./manage.py makemessages
# finds our text.
_ = lambda s: s

class WBN_RegistrationApp(AppBase):
    locations = None
    def __init__(self, router):
        super(WBN_RegistrationApp, self).__init__(router)
        #load locations
        try:
            f = open(LOCATIONS_FILE, 'r')
        except IOError:
            print 'We had na IOError? %s' % IOError.message
            print 'PATH:%s' % os.path.abspath(os.path.curdir)
            self._logger.log(logging.ERROR, 'Locations file "%s" was not found in the app directory (WBN_REGISTRATION)' % LOCATIONS_FILE )
            raise IOError

        lines = ''.join(f.readlines())
        self.locations = json.loads(lines)
        f.close()

    locations = None
    def start(self):
        self.info('Starting WBN_Regsitration App')

    def handle(self, msg):
        """
        This app is for basic user registration using a location code.
        User send in *only* the location code.  We respond with a request to
        confirm that they indeed want this location.  They respond with 1 or 2 (Yes or No)
        and we finalize the registration, or delete and start fresh, respectively.
        """
        if msg.text.lower() == "loc":
            msg.respond("Locations:%s" % str(self.locations))

        wbu = None
        try:
            #We will find a WBUser if they have sent in a location code but haven't done the final confirmation
            wbu = WBUser.objects.get(connection=msg.connection, location_code=msg.text.lower(), is_registered=False)
        except ObjectDoesNotExist:
            pass

        if wbu:
            #Verify that they are confirming or rejecting this location as 'theirs'
            if msg.text.lower() != "1" or msg.text.lower() != "2":
                msg.respond('Sorry, please send 1 for Yes or 2 for No')
                return True
            if msg.text.lower() == "1":
                wbu.is_registered = True
                wbu.save()
                msg.respond('Great! Thanks for registering! We will be in touch shortly')
                return True
            else:
                wbu.delete()
                msg.respond("Ok.  Please try registering again with the correct location code")
                return True

        #Initial registration process (user sends in a location code)
        if msg.text.lower() in self.locations:
            loc = self.locations[msg.text.lower()]
            try:
                wbu = WBUser.objects.get(connection=msg.connection, location_code=msg.text.lower())
                if wbu.is_registered:
                    msg.respond('You are already registered for this location! %s' % loc)
                    return True
            except ObjectDoesNotExist:
                pass
            #Create WB User
            wbu = WBUser(connection=msg.connection, is_registered=False, location_code = msg.text.lower())
            wbu.save()
            msg.respond(_('Thanks for registering! Is your location %s? Send 1 for YES and 2 for NO' % self.locations[msg.text.lower()]))
            return True
