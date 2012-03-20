from rapidsms.apps.base import AppBase
from django.core.exceptions import ObjectDoesNotExist
from rapidsms.messages import OutgoingMessage
from fakit import fakit
from models import XFormsSession, XFormSurvey
from datetime import datetime

class TouchFormsApp(AppBase):

    f = None

    def start(self):
        self.f = fakit()
        self.info('Started TouchFormsApp')

    def handle(self, msg):
        print msg.text
        #check if this contact is in a form session:
        session = None
        try:
            print 'down in there'
            session = XFormsSession.objects.get(contact=msg.contact)
            print 'fucking failing silently'
        except ObjectDoesNotExist:
            print 'up in here'
        if not session:
            print 'MSG TEXT WAS: %s, == "startform"? %s' % (msg.text, msg.text=='startform')
            if msg.text == 'startform':
                #create a session
                try:
                    session = XFormsSession(start_date=datetime.now(), touch_time=datetime.now(), contact=msg.contact)
                except:
                    raise Exception('SHIT!')
                session.session_id = self.f.start_session()
                session.started = True
                session.save()
                msg.respond(self.f.get_question(session.session_id))
                print 'sent a response message'
                return True
                #start a form
            else:
                print 'MSG TEXT WAS: %s, == "startform"? %s' % (msg.text, msg.text=='startform')
                return
        else:
            ans = msg.text
            if ans == 'get_question':
                session.touch_time = datetime.now()
                session.save()
                msg.respond(self.f.get_question(session.session_id))
                return True

            resp = self.f.give_answer(session.session_id, ans)
            if resp != 'CORRECT_ANSWER':
                session.touch_time = datetime.now()
                session.save()
                msg.respond(resp)
            elif resp == 'DONE':
                msg.respond("Congratulations! You're done.")
                session.touch_time = datetime.now()
                session.end_date = datetime.now()
                session.save()
            else:
                #I don't think we should ever get here.
                self.error("WE'RE NOT SUPPOSED TO BE THIS FAR DOWN IN THE ELSE TREE in smstouchforms/app.py")
                msg.respond(self.f.get_question(session.session_id))