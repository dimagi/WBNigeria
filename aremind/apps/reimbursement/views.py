#import calendar
#import datetime
from collections import defaultdict
import logging

from django.db.models.aggregates import Max
from django.conf import settings
from django.http import HttpResponse

from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend, Connection
from rapidsms.messages.outgoing import OutgoingMessage
from threadless_router.router import Router
#from rapidsms.router import router

from aremind.apps.reimbursement.models import Batch, ReimbursementRecord, Subscriber, REIMBURSEMENT_RATES, NAME_NETWORK_MAP, REIMBURSEMENT_NUMBERS
from aremind.apps.dashboard.utils.shared import network_for_number


def get_next_batch(request):
    '''
    Get next batch of reimbursements
    '''
    total_messages = next_batch()
    return HttpResponse('%s messages'%total_messages)

def start_reimbursement(request):
    '''
    Start processing pending reimbursements.

    Only one per network can be processing
    '''
    total_started = reimburse()
    return HttpResponse('%s reimbursements started'%total_started)

def next_batch():
    '''
    Extract the count of new messages per number for reimbursement
    '''
    last_time = Batch.objects.aggregate(max_time=Max('last_time'))['max_time']
    #import pdb;pdb.set_trace()
    if not last_time:
        batch = Batch.objects.create()
        last_time = batch.last_time

    max_date = None
    messages = Message.objects.filter(date__gt=last_time, direction="I")
    if not messages:
        return 0

    msg_counter = defaultdict(int)
    max_date = max([msg.date for msg in messages])
    for msg in messages:
        if msg.connection.backend.name in settings.REIMBURSED_BACKENDS:
            msg_counter[msg.connection.identity[-10:]] += 1

    total_messages = sum([v for k,v in msg_counter.items()])

    Batch.objects.create(last_time=max_date)

    for number, msg_count in msg_counter.items():
        logging.info('number: %s, msg_count: %s'%(number, msg_count))
        number = '234%s' % number
        network = network_for_number(number)
        #import pdb;pdb.set_trace()
        if network and len(number) == 13:#using the full 2348... format of 13 digits
            try:
                subscriber = Subscriber.objects.get(number=number)
                #reimbursement = Reimbursement.objects.get(
                #        number=number,
                #        status=Reimbursement.PENDING,
                #        )
            except Subscriber.DoesNotExist:
                Subscriber.objects.create(
                    number=number,
                    balance=REIMBURSEMENT_RATES[network]*msg_count,
                    network=NAME_NETWORK_MAP[network])
            else:
                subscriber.balance += REIMBURSEMENT_RATES[network]*msg_count
                subscriber.save()
    return total_messages

def reimburse():
    '''
    Start reimbursement process, entailing interaction with special numbers
    '''
    counter = 0
    network_name_map = dict([(v, k) for k, v in NAME_NETWORK_MAP.items()])
    reimbursements = ReimbursementRecord.objects.exclude(
            status__in=(ReimbursementRecord.COMPLETED, ReimbursementRecord.ERROR)
            )

    #import pdb;pdb.set_trace()
    for network, _ in Subscriber.NETWORKS:
        print 'network: %s'%network
        if reimbursements.filter(
                status__in=(
                    ReimbursementRecord.IN_PROGRESS, ReimbursementRecord.QUEUED),
                subscriber__network=network):
            continue
        else:
            #there is no reimbursement in progress for "network"
            subscribers = Subscriber.objects.filter(balance__gt=0, network=network)
            if subscribers:
                subscriber = subscribers[0]
            else:
                continue

            network_name = network_name_map.get(network)
            _amount = max(subscriber.balance, settings.MINIMUM_TRANSFERS.get(network_name))
            backend_name = subscriber.get_backend()
            backend, _ = Backend.objects.get_or_create(name=backend_name)
            text = subscriber.first_message % {
                    'number': '0%s'%subscriber.number[-10:],
                    'amount': _amount,
                    'pin': settings.NETWORK_PINS.get(network_name)
                    }
            logging.info('message to send is %s'%text)
            to_number = REIMBURSEMENT_NUMBERS.get(network_name)
            if len(to_number) < 11:#If it is a short-code, prefix with 's'
                to_number = 's%s'%to_number
            connection, _ = Connection.objects.get_or_create(
                    backend=backend, identity=to_number)
            msg = OutgoingMessage(connection=connection, template=text)
            try:
                msg.send()
            except:
                router = Router()
                #router.start()
                router.outgoing(msg)
            ReimbursementRecord.objects.create(
                subscriber=subscriber,
                amount=_amount,
                status=ReimbursementRecord.IN_PROGRESS)
            counter += 1
    return counter

