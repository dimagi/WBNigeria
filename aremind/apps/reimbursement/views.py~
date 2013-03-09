#import calendar
import datetime
from collections import defaultdict

from django.db.models.aggregates import Max
from django.conf import settings
from django.http import HttpResponse

from rapidsms.contrib.messagelog.models import Message
from rapidsms.models import Backend, Connection
from rapidsms.messages.outgoing import OutgoingMessage
from threadless_router.router import Router
#from rapidsms.router import router

from aremind.apps.reimbursement.models import Batch, Reimbursement, REIMBURSEMENT_RATES, NAME_NETWORK_MAP, REIMBURSEMENT_NUMBERS
from aremind.apps.dashboard.utils.shared import network_for_number


def get_next_batch(request):
    '''
    Get next batch of reimbursements
    '''
    last_time = Batch.objects.aggregate(last_batch=Max('last_time'))['last_batch']
    if not last_time:
        batch = Batch.objects.create()
        last_time = batch.last_time
    msg_counter = defaultdict(int)
    for msg in Message.objects.filter(date__gte=last_time, direction="I"):
        if msg.connection.backend.name in settings.REIMBURSED_BACKENDS:
            msg_counter[msg.connection.identity] += 1

    new_batch = Batch.objects.create()
    for number, msg_count in msg_counter.items():
        network = network_for_number(number)
        if network and len(number) >= 10:
            Reimbursement.objects.create(
                    batch=new_batch,
                    number=number,
                    amount=REIMBURSEMENT_RATES[network]*msg_count,
                    network=NAME_NETWORK_MAP[network])
    total = new_batch.reimbursements.count()
    return HttpResponse('total: %s'%total)

def start_reimbursement(request):
    '''
    Start processing pending reimbursements.

    Only one per network can be processing
    '''
    counter = 0
    network_name_map = dict([(v, k) for k, v in NAME_NETWORK_MAP.items()])
    reimbursements = Reimbursement.objects.exclude(status__in=(Reimbursement.COMPLETED, Reimbursement.ERROR)).order_by('batch')
    #import pdb;pdb.set_trace()
    for network, _ in Reimbursement.NETWORKS:
        #print 'network: %s'%network
        if reimbursements.filter(
                status__in=(
                    Reimbursement.IN_PROGRESS, Reimbursement.QUEUED),
                network=network):
            continue
        else:
            #get earliest batch
            pending = reimbursements.filter(network=network, status=Reimbursement.PENDING)
            if pending:
                reimburse = pending[0]
                ##queue reimbursement
                #reimburse.status = Reimbursement.QUEUED
                #reimburse.save()

                backend_name = reimburse.get_backend()
                backend, _ = Backend.objects.get_or_create(name=backend_name)
                network_name = network_name_map.get(network)

                text = reimburse.first_message % {
                        'number': '0%s'%reimburse.number[-10:],
                        'amount': reimburse.amount,
                        'pin': settings.NETWORK_PINS.get(network_name)
                        }
                to_number = REIMBURSEMENT_NUMBERS.get(network_name)
                connection, _ = Connection.objects.get_or_create(backend=backend, identity=to_number)
                msg = OutgoingMessage(connection=connection, template=text)
                try:
                    msg.send()
                except:
                    router = Router()
                    #router.start()
                    router.outgoing(msg)
                reimburse.status = Reimbursement.IN_PROGRESS
                reimburse.save()
                counter += 1
    return HttpResponse('%s queued'%counter)

