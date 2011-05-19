# input parameters:
#   number_to_call   e.g. "+19195551212"  (no - etc)
#   patient_id
#   callback_url
#   caller_id   e.g. "+19195551212"  (no - etc)
#   network
#   use_recordings   # 1 or 0
#   message_url   # base URL for recordings of messages, ends in /

from urllib import urlencode
from urllib2 import urlopen

def fix_number(num):
    num = num.strip()
    if num[0] != '+':
        num = "+" + num
    num = num.replace("-","").replace("(","").replace(")","")
    return num

number_to_call = fix_number(number_to_call)
caller_id = fix_number(caller_id)

if int(use_recordings):
    welcome_msg = message_url + "welcome.gsm"
    question1_msg = message_url + "question1.wav"
    badchoice_msg = message_url + "badchoice.wav"
else:
    welcome_msg = "Hello. This is ARemind.  We're calling to check how you're doing with medications."
    question1_msg = "How many pills did you take yesterday? Please press the number on your phone."
    badchoice_msg = "Sorry, I didn't understand that."

if network == 'SMS':
    timeout = 300 # seconds
else:
    timeout = 20 # seconds

def onBadChoice(event):
    say(badchoice_msg)

def onTimeout(event):
    """This event fires when the user doesn't respond to the prompt within a specified period of time."""
    # just repeat question
    say(question)

parms = {'callerID':caller_id}
if network == 'SMS':
    parms['network'] = network
log("calling '%s' with parms %r" % (number_to_call, parms))
result = call(number_to_call,parms)
log('result=%r' % result)

if result.name == 'answer':
    # call was good
    say(welcome_msg)
    question = question1_msg
    result = ask(question,
                 { 'attempts': 3,
                   'choices': "[1 DIGIT]",
                   'mode': 'dtmf',
                   'onBadChoice': onBadChoice,
                   'timeout': timeout, # float seconds
                   })
    say("Thank you")
    hangup()

# see what happened
if result.name == 'choice':
    # Good, we got a valid answer
    params = urlencode([('status','good'),
                        ('answer',result.value),
                        ('patient_id',patient_id),])
else:
    # Nope
    params = urlencode([('status','bad'),
                        ('patient_id',patient_id),])
try:
    urlopen("%s?%s" % (callback_url, params)).read()
except NameError, e:
    log(e)
