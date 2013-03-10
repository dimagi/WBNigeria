# vim: ai ts=4 sts=4 et sw=4
import logging
import datetime

from django.db import models


#logger = logging.getLogger('broadcast.models')


AIRTEL_MESSAGE_LIST = [
        {
            'message': '2u %(number)s %(amount)s %(pin)s',
            'response': 'Ref ID',
            'errors': []
        },
    ]
MTN_MESSAGE_LIST = [
        {
            'message': 'Transfer %(number)s %(amount)s %(pin)s',
            'response': 'You are sending',
            'errors': {
                'Sorry, you still have an open transaction': 'Yes'
                }
        },
        {
            'message': 'Yes',
            'response': 'You transferred',
        }
    ]

ETISALAT_MESSAGE_LIST = [
        {
            'message': 'Credit %(number)s with %(amount)s'
        }
    ]
MTN_MSG_RESPONSE = {
        'You are sending': 'Yes',
        'Sorry, you still have an open transaction': 'Yes',
        #'You transferred': '',
        }


class Batch(models.Model):
    last_time = models.DateTimeField(default=datetime.datetime.now)

    class Meta:
        verbose_name_plural = 'Batches'

    def __unicode__(self):
        return self.last_time.strftime('%d-%m-%Y %H:%M:%S')

    @property
    def count(self):
        return self.reimbursements.count()

class Reimbursement(models.Model):
    MTN = 0
    AIRTEL = 1
    ETISALAT = 2
    NETWORKS = list(enumerate(('MTN', 'Airtel', 'Etisalat')))

    PENDING = 0
    QUEUED = 1
    IN_PROGRESS = 2
    COMPLETED = 3
    ERROR = 4
    REIMBURSEMENT_STATUSES = enumerate(('Pending', 'Queued', 'In Progress', 'Completed', 'Error'))

    batch = models.ForeignKey(Batch, related_name='reimbursements')
    number = models.CharField(max_length=20)
    amount = models.PositiveIntegerField()
    network = models.PositiveIntegerField(choices=NETWORKS)
    status = models.PositiveIntegerField(choices=REIMBURSEMENT_STATUSES, default=PENDING)
    last_message = models.TextField(blank=True)

    def __unicode__(self):
        return self.number

    def get_backend(self):
        if self.network == self.MTN:
            return 'smstools-mtn'
        elif self.network == self.AIRTEL:
            return 'smstools-airtel'
        elif self.network == self.ETISALAT:
            return 'smstools-etisalat'

    @property
    def first_message(self):
        if self.network == self.AIRTEL:
            return AIRTEL_MESSAGE_LIST[0].get('message')
        elif self.network == self.MTN:
            return MTN_MESSAGE_LIST[0].get('message')
        else:
            return ETISALAT_MESSAGE_LIST[0].get('message')

    def add_message(self, txt, direction='Incoming'):
        self.last_message += '\n%s: %s'%(direction, txt)
        super(Reimbursement, self).save()

REIMBURSEMENT_NUMBERS = {
    'mtn': '777',
    'airtel': '432',
    'etisalat': '2348172160308',
    }

REIMBURSEMENT_RATES = {
    'mtn': 4,
    'airtel': 4,
    'etisalat': 4,
    }

NAME_NETWORK_MAP = {
    'mtn': Reimbursement.MTN,
    'airtel': Reimbursement.AIRTEL,
    'etisalat': Reimbursement.ETISALAT
    }
