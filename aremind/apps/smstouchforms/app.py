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
        print 'LOGGER NAME %s' % self._logger_name()
        def _next(xformsresponse, message, session):
            # if there's a valid session id (typically on a new form)
            # update our mapping
            self.debug('QUESTION RESPONSE: %s' % response)
            session.current_response = response
            session.save()
            if xformsresponse.event.type == "question":
                # send the next question
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
            session = XFormsSession.objects.get(connection=msg.connection)
        except ObjectDoesNotExist:
            pass
        if not session:
            if not msg.text.lower().startswith('startform'):
                return

            #create a session
            session = XFormsSession(start_time=datetime.now(), touch_time=datetime.now(), connection=msg.connection, ended=False)
            form_id = int(msg.text.split()[1])
            form = XForm.objects.get(pk=form_id)
            response = api.start_form_session(form.file.path)
            session.session_id = response.session_id
            session.started = True
            session.save()
            return _next(response, msg, session)
        else:
            def _format(text):
                # touchforms likes ints to be ints so force it if necessary
                try:
                    return int(text)
                except ValueError:
                    return text

            response = api.answer_question(int(session.session_id),_format(msg.text))
            return _next(response, msg, session)