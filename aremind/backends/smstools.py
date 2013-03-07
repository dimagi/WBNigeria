from django.http import HttpResponse

from threadless_router.backends.kannel.forms import KannelForm
from threadless_router.backends.kannel.views import KannelBackendView

class SmsToolsBackendView(KannelBackendView):

    http_method_names = ['get']
    form_class = KannelForm
    backend_name = 'smstools'

    def get(self, *args, **kwargs):
        kwargs['backend_name'] = 'smstools'
        return self.post(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(SmsToolsBackendView, self).get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def form_valid(self, form):
        super(SmsToolsBackendView, self).form_valid(form)
        return HttpResponse('')
