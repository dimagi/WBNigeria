from rapidsms.apps.base import AppBase
from django.core.exceptions import ObjectDoesNotExist
from models import XFormsSession
from datetime import datetime
from touchforms.formplayer import api
from touchforms.formplayer.models import XForm
import json

class TouchFormsApp(AppBase):
    def start(self):
        self.info('Started TouchFormsApp')

    def handle(self, msg):
        def _next(xformsresponse, message, session):
            # if there's a valid session id (typically on a new form)
            # update our mapping
            self.debug('QUESTION RESPONSE: %s' % response)
            session.current_response = response
            session.save()
            if xformsresponse.event.type == "question":
                # send the next question
                session.touch_time = datetime.now()
                session.save()
                message.respond(xformsresponse.event.text_prompt)
                return True
            elif xformsresponse.event.type == "form-complete":
                message.respond("you're done! thanks!")
                session.end_time = datetime.now()
                session.ended = True
                session.save()
                return True

        #check if this Connection is in a form session:
        session = None
        try:
            session = XFormsSession.objects.get(connection=msg.connection, ended=False)
        except ObjectDoesNotExist:
            pass
        if not session:
            words = msg.text.lower().split()
            if len(words) == 1 and (words[0] == 'fadama' or words[0] == 'health'):
                #create a session
                session = XFormsSession(start_time=datetime.now(), touch_time=datetime.now(), connection=msg.connection, ended=False)
                if words[0] == 'fadama':
                    form_id = 4
                else:
                    form_id = 3
                form = XForm.objects.get(pk=form_id)
                response = api.start_form_session(form.file.path)
                session.session_id = response.session_id
                session.started = True
                session.save()
                return _next(response, msg, session)
            else:
                return None
        else:
            def _format(text):
                # touchforms likes ints to be ints so force it if necessary
                try:
                    return int(text)
                except ValueError:
                    return text

            response = api.answer_question(int(session.session_id),_format(msg.text))
            return _next(response, msg, session)