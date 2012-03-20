import uuid

answer_list = [
    "pandas",
    "foo",
    "1",
    "yay"
]

question_list = [
    "The answer is pandas?",
    "The answer is foo?",
    "Send 1",
    "You're almost done, say yay"
]


class fakit():
    state_dict = None

    def __init__(self):
        self.state_dict = dict()

    def start_session(self):
        ses_uuid = uuid.uuid1()
        self.state_dict[ses_uuid] = None
        return ses_uuid

    def _check_session(self, sessionid):
        if not sessionid:
            return 'No Session ID given, not doing anything'

        if not self.state_dict.__contains__(sessionid):
            return "This session isn't recognized, start a new one"

        return "valid"

    def get_question(self, sessionid):
        is_valid = self._check_session(sessionid)
        if is_valid != "valid":
            return is_valid

        current_answer = self.state_dict[sessionid]
        if current_answer == answer_list[len(answer_list)-1]:
            return 'DONE'
        if current_answer == None:
            return question_list[0]
        else:
            return question_list[answer_list.index(current_answer) + 1]


    def give_answer(self, sessionid, answer):
        is_valid = self._check_session(sessionid)
        if is_valid != "valid":
            return is_valid

        current_question = self.get_question(sessionid)
        q_idx = question_list.index(current_question)

        if answer != answer_list[q_idx]:
            return 'Wrong answer! Try again! Send get_question to resend question'
        else:
            self.state_dict[sessionid] = answer
            return 'CORRECT_ANSWER'