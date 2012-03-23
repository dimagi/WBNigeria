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
    def _logger_name(self):
        return "app.%s" % self.name

    STRING_REG_CONFIRMED = _('Great! Thanks for registering! We will be in touch shortly')
    STRING_REG_REQUEST_YESNO = _('Sorry, please send 1 for Yes or 2 for No')
    STRING_REG_RESPONSE_BAD_LOC = _("Ok.  Please try registering again with the correct location code")
    STRING_REG_ALREADY_REGISTERED = _('You are already registered for this location! %s')
    STRING_REG_REQUEST_CONFIRM = _('Thanks for registering! Is your location %s? Send 1 for YES and 2 for NO')

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
        self.debug('In WBN Registration app')
        if msg.text.lower() == "loc":
            msg.respond("Locations:%s" % str(self.locations))

        #We will find a WBUser if they have sent in a location code but haven't done the final confirmation
        wbu = WBUser.objects.filter(connection=msg.connection, is_registered=False)
        if wbu.count() > 0:
            wbu = wbu[0] #just grab the first unconfirmed one. TODO: we should probably clear out hanging unconfirmed regs periodically
            self.debug('Found a WBUser. State, is_registered=False: %s' % wbu)
        else:
            wbu = None
            self.debug('No WBUser object found for this connection. Needs to freshly register')

        if wbu:
            #Verify that they are confirming or rejecting this location as 'theirs'
            if msg.text.lower() != "1" and msg.text.lower() != "2":
                self.debug('User did not send "1" or "2", we ask them to do so. They sent: "%s" isinstance(msg.text,int)? %s' % (msg.text, isinstance(msg.text, int)))
                msg.respond(self.STRING_REG_REQUEST_YESNO)
                return True
            if msg.text.lower() == "1":
                self.debug('User sent a "1", confirm their registration')
                wbu.is_registered = True
                wbu.save()
                msg.respond(self.STRING_REG_CONFIRMED)
                return True
            else:
                self.debug('User sent a "2", so delete their WBUser object and have them start from the top')
                wbu.delete()
                msg.respond(self.STRING_REG_RESPONSE_BAD_LOC)
                return True

        #Initial registration process (user sends in a location code)
        if msg.text.lower() in self.locations:
            self.debug('User sent in a location registration code')
            loc = self.locations[msg.text.lower()]
            try:
                wbu = WBUser.objects.get(connection=msg.connection, location_code=msg.text.lower())
                if wbu.is_registered:
                    self.debug('User is already registered + confirmed for this location')
                    msg.respond(self.STRING_REG_ALREADY_REGISTERED % loc)
                    return True
            except ObjectDoesNotExist:
                pass
            #Create WB User
            self.debug('Creating a new WBUser object for this contact and asking for confirmation of location')
            wbu = WBUser(connection=msg.connection, is_registered=False, location_code = msg.text.lower())
            wbu.save()
            msg.respond(_(self.STRING_REG_REQUEST_CONFIRM % self.locations[msg.text.lower()]))
            return True
