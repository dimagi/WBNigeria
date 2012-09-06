import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


class LoginMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginMixin, self).dispatch(request, *args, **kwargs)


class ReportMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context['default_site'] = kwargs.get('site')
        context['default_metric'] = kwargs.get('metric')
        return context


class APIMixin(object):
    def get_user_state(self):
        """return state for logged-in user, None for national user (or mis-configured)"""
        try:
            contact = self.request.user.contact_set.all()[0]
        except IndexError:
            return None

        loc = contact.location
        if not loc:
            return None

        if loc.type.slug != 'state':
            return None

        return loc.slug

    def get(self, request, *args, **kwargs):
        _site = request.GET.get('site')
        site = int(_site) if _site else None

        payload = self.get_payload(site)
        return HttpResponse(json.dumps(payload), mimetype='application/json')
