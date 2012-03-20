from fakit import fakit

f = fakit()
session = f.start_session()
ans = None
resp = None
while True:
    if f.get_question(session) == 'DONE':
        break
    print f.get_question(session)
    ans = raw_input("Enter answer:")
    resp = f.give_answer(session,ans)
    print 'Response: %s' % resp


