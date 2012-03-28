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

    STRING_REG_CONFIRMED = _('Great! Thanks for registering! How was your service rendered to you?')
    STRING_REG_REQUEST_YESNO = _('Sorry, please send 1 for Yes or 2 for No')
    STRING_REG_RESPONSE_BAD_LOC = _("Ok.  Please try registering again with the correct location code")
    STRING_REG_ALREADY_REGISTERED = _('You are already registered for this location: %s. To unregister send \'unregister\' LOCATION_CODE')
    STRING_REG_REQUEST_CONFIRM = _('Thanks for registering! Is your location %s? Send 1 for YES and 2 for NO')
    STRING_SURVEY_ANS = _('Thanks for your response! Would you like to participate in other tests? Send 1 for YES and 2 for NO')
    DOES_WANT_MORE_SURVEY = _('OK. Thanks for trying our system!')
    DOES_NOT_WANT_MORE_SURVEY = _('OK. Thanks for trying our system!')
    STANDARD_ERROR = _('The system did not understand. Please try again.')

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

    def handle_list_register(self,msg):
        if msg.text.lower().strip() != 'list register':
            return
        locs = []
        wbu = WBUser.objects.filter(connection=msg.connection, is_registered=True)
        for w in wbu:
            locs.append((w.location_code, self.locations[w.location_code],))
        if len(locs) == 0:
            msg.respond('You are not registered at any locations!')
        else:
            out = 'You are registered at the following locations:'
            for loc in locs:
                out += '%s(%s),' % (loc[1], loc[0])
            msg.respond(out)
            return True


    def handle_unregister(self, msg):
        words = msg.text.lower().split()
        if len(words) <= 0:
            return None
        if words[0] != 'unregister' and words[0] != 'u':
            return None

        if len(words) == 1:
            msg.respond('Must include location code to unregister! To list everywhere you are registered send: list register')

        loc_code = words[1]
        try:
            wbu = WBUser.objects.get(connection=msg.connection, location_code=loc_code, is_registered=True)
        except ObjectDoesNotExist:
            msg.respond('You are either not registered for this location or you sent a bad code')
            return True

        wbu.delete()
        msg.respond('You have succesfully unregistered at %s.' % self.locations[loc_code])
        return True


    def handle(self, msg):
        """
        This app is for basic user registration using a location code.
        User send in *only* the location code.  We respond with a request to
        confirm that they indeed want this location.  They respond with 1 or 2 (Yes or No)
        and we finalize the registration, or delete and start fresh, respectively.
        """
        self.debug('In WBN Registration app')

        ret = self.handle_unregister(msg)
        if ret:
            return ret

        ret = self.handle_list_register(msg)
        if ret:
            return ret


        #We will find a WBUser if they have sent in a location code but haven't done the final confirmation
        wbu = WBUser.objects.filter(connection=msg.connection)
        if wbu.count() > 0:
            wbu = wbu[0] #just grab the first unconfirmed one. TODO: we should probably clear out hanging unconfirmed regs periodically
            self.debug('Found a WBUser. State, is_registered=False: %s' % wbu)
        else:
            wbu = None
            self.debug('No WBUser object found for this connection. Needs to freshly register')

        if wbu:
            #Verify that they are confirming or rejecting this location as 'theirs'
            if msg.text.lower() != "1" and msg.text.lower() != "2" and msg.text.lower() != "3":
                self.debug('User did not send "1" or "2" or "3", we ask them to do so. They sent: "%s" isinstance(msg.text,int)? %s' % (msg.text, isinstance(msg.text, int)))
                msg.respond(self.STANDARD_ERROR)
                return True
            if msg.text.lower() == "1":
                if not wbu.is_registered:
                    self.debug('User sent a "1", confirm their registration')
                    wbu.is_registered = True
                    wbu.save()
                    msg.respond(self.STRING_REG_CONFIRMED)
                    return True
                elif wbu.is_registered and not wbu.survey_question_ans:  #registered and now answering post-survey question
                    self.debug('User sent a "1", to respond to the survey question post survey')
                    wbu.survey_question_ans = msg.text
                    wbu.save()
                    msg.respond(self.STRING_SURVEY_ANS)
                    return True
                else: #user is reg'd, has answered the initial post survey question and is responding to the queury about them wanting to participate more
                    self.debug("user is reg'd, has answered the initial post survey question and is responding to the queury about them wanting to participate more (ans:'1')")
                    wbu.want_more_surveys = True
                    wbu.save()
                    msg.respond(self.DOES_WANT_MORE_SURVEY)
                    return True
            elif msg.text.lower() == "2":
                if not wbu.is_registered:
                    self.debug('User sent a "2", so delete their WBUser object and have them start from the top')
                    wbu.delete()
                    msg.respond(self.STRING_REG_RESPONSE_BAD_LOC)
                    return True
                elif wbu.is_registered and not wbu.survey_question_ans:  #registered and now answering post-survey question
                    self.debug('User sent a "2", to respond to the survey question post survey')
                    wbu.survey_question_ans = msg.text
                    wbu.save()
                    msg.respond(self.STRING_SURVEY_ANS)
                    return True
                else:
                    self.debug("user is reg'd, has answered the initial post survey question and is responding to the queury about them wanting to participate more (ans:'2')")
                    wbu.want_more_surveys = False
                    wbu.save()
                    msg.respond(self.DOES_NOT_WANT_MORE_SURVEY)
                    return True
            elif msg.text.lower() == "3":
                if wbu.is_registered and not wbu.survey_question_ans:
                    self.debug('User sent a "3", to respond to the survey question post survey')
                    wbu.survey_question_ans = msg.text
                    wbu.save()
                    msg.respond(self.STRING_SURVEY_ANS)
                    return True
                else:
                    msg.respond(self.STANDARD_ERROR)
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
