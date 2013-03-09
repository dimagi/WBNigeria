#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings

from rapidsms.apps.base import AppBase
from rapidsms.messages import OutgoingMessage
from rapidsms.models import Backend, Connection

from aremind.apps.reimbursement.models import Reimbursement, NAME_NETWORK_MAP, REIMBURSEMENT_NUMBERS
import logging


class ReimburseApp(AppBase):
    '''
    App to do reimbursement for incoming messages
    '''

    def start(self):
        self.info('started')

    def handle(self, msg):
        #msg_parts = msg.text.split()
        #self.send_queued_messages()
        backend = msg.connection.backend
        logging.debug('msg: %s'%msg.text)
        #import pdb;pdb.set_trace()
        return True

    def send_queued_messages(self):
        '''
        Send all queued messages
        '''
        network_name_map = dict([(v, k) for k, v in NAME_NETWORK_MAP.items()])
        for reimburse in Reimbursement.objects.filter(status=Reimbursement.QUEUED):
            backend_name = reimburse.get_backend()
            backend, _ = Backend.objects.get_or_create(name=backend_name)
            network_name = network_name_map.get(reimburse.network)

            text = reimburse.first_message % {
                     'number': '0%s'%reimburse.number[-10:],
                     'amount': reimburse.amount,
                     'pin': settings.NETWORK_PINS.get(network_name)
                     }
            to_number = REIMBURSEMENT_NUMBERS.get(network_name)
            connection = Connection.objects.create(backend=backend, identity=to_number)
            msg = OutgoingMessage(connection=connection, template=text)
            self.router.outgoing(msg)
        reimburse.status = Reimbursement.IN_PROGRESS
        reimburse.save()

