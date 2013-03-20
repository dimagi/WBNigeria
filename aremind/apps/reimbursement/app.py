#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings

from rapidsms.apps.base import AppBase
from rapidsms.messages import OutgoingMessage
#from rapidsms.models import Connection
from datetime import datetime

from aremind.apps.reimbursement.models import ReimbursementRecord, ReimbursementLog, NAME_NETWORK_MAP, REIMBURSEMENT_NUMBERS, AIRTEL_MESSAGE_LIST, MTN_MSG_RESPONSE


class ReimburseApp(AppBase):
    '''
    App to do reimbursement for incoming messages
    '''

    def start(self):
        self.info('started')

    def handle(self, msg):
        #self.send_queued_messages()
        backend = msg.connection.backend
        #import pdb;pdb.set_trace()
        if backend.name in settings.REIMBURSED_BACKENDS:
            network_name = backend.name.split('-')[1]
            network_id = NAME_NETWORK_MAP.get(network_name)
            if msg.connection.identity == REIMBURSEMENT_NUMBERS.get(network_name):
                try:
                    current = ReimbursementRecord.objects.get(
                        status=ReimbursementRecord.IN_PROGRESS,
                        subscriber__network=network_id)
                except ReimbursementRecord.DoesNotExist:
                    pass
                else:
                    status = getattr(self, 'handle_%s'%network_name)(msg, current)
                    current.status = status
                    current.add_message(msg.text)

                    if status == ReimbursementRecord.COMPLETED:
                        current.subscriber.balance -= current.amount
                        current.subscriber.save()
                        current.completed_on = datetime.now()
                        ReimbursementLog.objects.create(
                            phone=current.subscriber.number,
                            amount=current.amount,
                            reimbursed_on=datetime.now())

                    current.save()
                return True #we always handle network credit transfer messages
        return False

    def handle_mtn(self, msg, current):
        #import pdb;pdb.set_trace()
        msg_text = msg.text
        connection = msg.connection
        for key, val in MTN_MSG_RESPONSE.items():
            if msg_text.startswith(key):
                out_msg = OutgoingMessage(connection=connection, template=val)
                self.router.outgoing(out_msg)
                return ReimbursementRecord.IN_PROGRESS
        if msg_text.startswith('You transferred'):
            return ReimbursementRecord.COMPLETED
        else:
            return ReimbursementRecord.ERROR

    def handle_airtel(self, msg, current):
        if msg.text.startswith(AIRTEL_MESSAGE_LIST[0]['response']):
            return ReimbursementRecord.COMPLETED
        else:
            return ReimbursementRecord.ERROR

    def handle_etisalat(self, msg, current):
        return ReimbursementRecord.IN_PROGRESS

    #def send_queued_messages(self):
    #    '''
    #    Send all queued messages
    #    '''
    #    network_name_map = dict([(v, k) for k, v in NAME_NETWORK_MAP.items()])
    #    for reimburse in ReimbursementRecord.objects.filter(status=Reimbursement.QUEUED):
    #        backend_name = reimburse.get_backend()
    #        backend, _ = Backend.objects.get_or_create(name=backend_name)
    #        network_name = network_name_map.get(reimburse.network)

    #        text = reimburse.first_message % {
    #                 'number': '0%s'%reimburse.number[-10:],
    #                 'amount': reimburse.amount,
    #                 'pin': settings.NETWORK_PINS.get(network_name)
    #                 }
    #        to_number = REIMBURSEMENT_NUMBERS.get(network_name)
    #        connection = Connection.objects.create(backend=backend, identity=to_number)
    #        msg = OutgoingMessage(connection=connection, template=text)
    #        self.router.outgoing(msg)
    #    reimburse.status = Reimbursement.IN_PROGRESS
    #    reimburse.save()

