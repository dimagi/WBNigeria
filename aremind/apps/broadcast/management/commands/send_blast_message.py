from django.core.management.base import LabelCommand, CommandError
from rapidsms.models import Connection
from rapidsms.messages import OutgoingMessage
from threadless_router.router import Router


class Command(LabelCommand):
    help = "Send a blast message to all users"
    args = "<message>"
    label = "The message to send."

    def handle(self, *args, **options):
        if len(args) != 1: raise CommandError('Please specify %s.' % self.label)

        message = args[0]
        all_connections = Connection.objects.all()
        success = []
        failed = []
        router = Router()
        for conn in all_connections:
            try:
                router.outgoing(OutgoingMessage(conn, message))
                success.append(conn)
            except Exception, e:
                print "failed to send to %s because %s" % (conn, e)
                failed.append(conn)

        print "sent to %s connections. %s failed." % (len(success), len(failed))

